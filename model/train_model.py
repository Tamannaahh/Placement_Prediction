import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib

# 1. Load Data
data = pd.read_csv('model/placement_data.csv')

# 2. Features (Inputs) and Target (Output)
X = data[['CGPA', 'Internships', 'Backlogs', 'CommunicationSkill']]
y = data['Placed']

# 3. Train the Model
# We use Random Forest because it handles complex student data well
model = RandomForestClassifier(n_estimators=100)
model.fit(X, y)

# 4. Save the Model
joblib.dump(model, 'model/placement_model.pkl')
print("Model trained and saved as 'placement_model.pkl'")