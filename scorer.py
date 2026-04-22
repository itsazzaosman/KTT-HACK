import pandas as pd
import numpy as np
import joblib
import argparse

def engineer_single_record(member_record, group_record): # process a single member and group record to produce the same features as in training
    """Applies the exact same feature engineering as the training notebook."""
    # Convert series to dataframes for easy manipulation
    df = pd.DataFrame([member_record]).merge(pd.DataFrame([group_record]), on='group_id', how='left')
    
    role_map = {'member': 0, 'secretary': 1, 'treasurer': 1}
    df['feat_role_seniority'] = df['role'].map(role_map) # write the role for each member as a feature (0 for regular members, 1 for secretary/treasurer)
    
    df['join_date'] = pd.to_datetime(df['join_date'])
    df['feat_tenure_months'] = (pd.Timestamp.now() - df['join_date']).dt.days // 30 # calculate the tenure in months as a feature
    
    df['feat_repayment_ratio'] = np.where( # calculate the borrow to repay ratio as a feature (if borrowed is 0, set to 1. Otherwise, repaid / borrowed)
        df['borrowed_total_xaf'] > 0, # 1 if they reapid all or they never borrowed at all 
        df['repaid_total_xaf'] / df['borrowed_total_xaf'],
        1.0
    )
    
    missed_cols = [f'missed_count_m{i}' for i in range(1, 13)]
    missed_matrix = df[missed_cols].values
    df['feat_total_missed'] = df[missed_cols].sum(axis=1)
    
    weights = np.linspace(0.5, 2.0, 12)
    df['feat_recent_miss_score'] = (missed_matrix * weights).sum(axis=1)
    
    def get_max_streak(row):
        streak = max_streak = 0
        for val in row:
            if val == 0:
                streak += 1
                max_streak = max(max_streak, streak)
            else:
                streak = 0
        return max_streak
    
    df['feat_max_on_time_streak'] = df[missed_cols].apply(get_max_streak, axis=1)
    df['feat_contrib_vs_group'] = df['weekly_contrib_xaf'] / df['avg_contrib_xaf']
    
    df['feat_penalty_compliance'] = np.where(
        df['feat_total_missed'] > 0,
        df['penalty_paid_count'] / df['feat_total_missed'],
        1.0 
    )
    df['feat_urban'] = df['urban_flag']
    
    feature_cols = [col for col in df.columns if col.startswith('feat_')]
    return df[feature_cols]

def score(member_record, group_record):
    """Calculates reliability with shadow-scoring and group-risk weighting."""
    # 1. Safety Check: Load the model
    try:
        model = joblib.load('ikimina_xgb_model.pkl')
    except FileNotFoundError:
        print("Error: Model file not found. Ensure train.ipynb has been run.")
        return None

    # 2. Base Model Prediction
    features = engineer_single_record(member_record, group_record)
    base_prob = model.predict_proba(features)[:, 1][0]
    
    # 3. Stretch Goal: Group-Level Risk Multiplier
    # We penalize scores slightly if the group is less than 2 years old
    group_age_multiplier = 1.05 if group_record['founded_year'] > 2024 else 1.0
    adjusted_prob = min(base_prob * group_age_multiplier, 1.0)
    
    # 4. Convert to 0-100 Reliability Index
    final_score = int(np.round((1 - adjusted_prob) * 100))
    
    # 5. Stretch Goal: Shadow-Score Logic
    # If the member has < 4 months history, we provide a confidence interval
    tenure = features['feat_tenure_months'].values[0]
    if tenure < 4:
        lower_bound = max(0, final_score - 15)
        upper_bound = min(100, final_score + 10)
        return f"{final_score} (Shadow Range: {lower_bound}-{upper_bound})"
    
    return str(final_score)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ikimina Reliability Scorer")
    parser.add_argument("--member", type=int, required=True, help="Member ID to score")
    parser.add_argument("--group", type=str, required=True, help="Group ID to score")
    args = parser.parse_args()

    # Load the datasets to pull the specific member and group records
    members_df = pd.read_csv('ikimina_members.csv')
    groups_df = pd.read_csv('ikimina_groups.csv')

    # Add leading zero to group if necessary (e.g., '7' becomes 'G07')
    group_str = args.group if args.group.startswith('G') else f"G{int(args.group):02d}"

    member_record = members_df[members_df['member_id'] == args.member]
    group_record = groups_df[groups_df['group_id'] == group_str]

    if member_record.empty or group_record.empty:
            print(f"Error: Could not find Member {args.member} or Group {group_str} in the datasets.")
    else:
        # Get the result from the score function
        final_result = score(member_record.iloc[0], group_record.iloc[0])
        
        # Extract just the first number for the Tier comparison logic
        numeric_score = int(str(final_result).split(' ')[0])
        
        # Determine tier
        tier = "High Risk" if numeric_score <= 40 else "Watch" if numeric_score <= 70 else "Low Risk"
        
        print("\n" + "$"*40)
        print(f"  IKIMINA DIGITAL TRUST SCORER  ")
        print("$"*40)
        print(f"Member ID: {args.member}")
        print(f"Group ID:  {group_str}")
        print(f"Reliability Index: {final_result}")
        print(f"Risk Tier: {tier}")
        print("="*40 + "\n")