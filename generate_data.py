import pandas as pd
import numpy as np
from faker import Faker
import datetime

def generate_ikimina_data():
    # Initialization and Seeding
    np.random.seed(42)
    fake = Faker()
    Faker.seed(42)

    # Rwandan districts for local context
    districts = ['Gasabo', 'Nyarugenge', 'Kicukiro', 'Musanze', 'Rubavu', 'Huye', 'Rwamagana']
    urban_districts = ['Gasabo', 'Nyarugenge', 'Kicukiro']

 # generate groups (40 rows)
    groups_data = []
    for g_id in range(1, 41):
        district = np.random.choice(districts)
        groups_data.append({
            'group_id': f'G{g_id:02d}',
            'size': 0, # Will update after member assignment
            'avg_contrib_xaf': np.random.randint(500, 10001),
            'founded_year': np.random.randint(2015, 2024),
            'district': district,
            'urban_flag': 1 if district in urban_districts else 0
        })
    groups_df = pd.DataFrame(groups_data)

# generate members (500 rows)
    members_data = []
    # Distribute members across groups (~12-13 per group)
    group_assignments = np.random.choice(groups_df['group_id'], size=500)
    
    for m_id in range(1, 501):
        group_id = group_assignments[m_id - 1]
        group = groups_df[groups_df['group_id'] == group_id].iloc[0]
        
        # Contribution with ~15% noise
        weekly_contrib = np.clip(np.random.normal(group['avg_contrib_xaf'], group['avg_contrib_xaf'] * 0.15), 100, None)
        weekly_contrib = round(weekly_contrib, -1) # Round to nearest 10
        
        base_miss = np.random.beta(2, 20)
        

        missed_counts = []
        on_time_rates = []
        z = np.random.normal(0, 1) 
        
        for m in range(12):
            # AR(1) update
            z = 0.4 * z + np.random.normal(0, 1) * np.sqrt(1 - 0.4**2)
            # Map latent AR(1) state to a probability around base_miss
            p_miss = np.clip(base_miss + (z * 0.05), 0, 1) 
            
            # Assume 4 weeks per month
            missed_weeks = np.random.binomial(4, p_miss)
            missed_counts.append(missed_weeks)
            on_time_rates.append((4 - missed_weeks) / 4.0)

        #penalties logic
        total_missed = sum(missed_counts)
        penalties_recorded = np.random.binomial(total_missed, 0.50)
        penalties_paid = np.random.binomial(penalties_recorded, 0.70)
        unpaid_penalties = penalties_recorded - penalties_paid
        
        #borrowing logic (~30% borrow)
        borrowed_total = 0
        repaid_total = 0
        if np.random.rand() < 0.30:
            target_mean = 3 * weekly_contrib * 8
            #logNormal parameters for the target mean
            sigma = 0.5
            mu = np.log(target_mean) - (sigma**2 / 2)
            borrowed_total = round(np.random.lognormal(mean=mu, sigma=sigma), -1)
            # Random repayment amount (0% to 100% of borrowed)
            repaid_total = round(borrowed_total * np.random.uniform(0.0, 1.0), -1)

        # Dates and roles
        join_date = fake.date_between(start_date=datetime.date(int(group['founded_year']), 1, 1), end_date='today')
        
        member_dict = {
            'member_id': m_id,
            'join_date': join_date,
            'role': 'member', # Will correct secretary/treasurer below
            'weekly_contrib_xaf': weekly_contrib,
            'penalty_paid_count': penalties_paid,
            'borrowed_total_xaf': borrowed_total,
            'repaid_total_xaf': repaid_total,
            'group_id': group_id,
            'district': group['district'],
            'unpaid_penalties_temp': unpaid_penalties, # Used for labels, dropped later
            'total_missed_temp': total_missed # Used for labels, dropped later
        }
        
        # Add monthly columns
        for m in range(12):
            member_dict[f'on_time_rate_m{m+1}'] = round(on_time_rates[m], 2)
            member_dict[f'missed_count_m{m+1}'] = missed_counts[m]
            
        members_data.append(member_dict)

    members_df = pd.DataFrame(members_data)

    # Assign roles (1 secretary, 1 treasurer per group)
    for g_id in groups_df['group_id']:
        group_members = members_df[members_df['group_id'] == g_id].index
        if len(group_members) >= 2:
            members_df.loc[group_members[0], 'role'] = 'secretary'
            members_df.loc[group_members[1], 'role'] = 'treasurer'
            
    # Update group sizes
    group_sizes = members_df.groupby('group_id').size()
    groups_df['size'] = groups_df['group_id'].map(group_sizes)
    
# generate labels with a logistic function to achieve ~14% default rate
    # Calculate tenure in months for the logistic function
    today = datetime.date.today()
    tenure_months = members_df['join_date'].apply(lambda d: (today.year - d.year) * 12 + today.month - d.month)
    
    # Calculate borrow/repaid ratio (handle div by zero safely)
    borrow_ratio = np.where(members_df['borrowed_total_xaf'] > 0, 
                            members_df['repaid_total_xaf'] / members_df['borrowed_total_xaf'], 
                            1.0) # If didn't borrow, consider them perfectly safe on this metric
    
    # Logistic function setup: w1*missed + w2*unpaid_penalties - w3*repaid_ratio - w4*tenure + bias
    # Weights hand-tuned to get ~14% default rate
    z_logit = (
        0.15 * members_df['total_missed_temp'] + 
        0.30 * members_df['unpaid_penalties_temp'] - 
        2.00 * borrow_ratio - 
        0.02 * tenure_months + 
        0.5 
    )
    
    probabilities = 1 / (1 + np.exp(-z_logit))
    
    # Adjust bias dynamically to hit exactly ~14% positive rate constraint
    threshold = np.percentile(probabilities, 100 - 14)
    labels = (probabilities >= threshold).astype(int)
    
    labels_df = pd.DataFrame({
        'member_id': members_df['member_id'],
        'defaulted_within_6m': labels
    })

    members_df = members_df.drop(columns=['unpaid_penalties_temp', 'total_missed_temp'])


    groups_df.to_csv('ikimina_groups.csv', index=False)
    members_df.to_csv('ikimina_members.csv', index=False)
    labels_df.to_csv('labels.csv', index=False)
    
    print(f"Data generation complete!")
    print(f"-> Groups: {len(groups_df)} rows")
    print(f"-> Members: {len(members_df)} rows")
    print(f"-> Labels: {len(labels_df)} rows")
    print(f"-> Default Rate: {labels_df['defaulted_within_6m'].mean() * 100:.1f}% (Target: ~14%)")

if __name__ == "__main__":
    generate_ikimina_data()