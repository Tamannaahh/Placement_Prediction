# 🎓 PPSU Career+ (Smart-Placement Prediction System)

An AI-powered Placement Prediction and Management System designed to bridge the gap between academic preparation and industry requirements. This system uses Predictive Analytics to determine job suitability while providing students with an interactive, multimodal AI preparation environment.

---

## 🚀 Key Features

* **JobFit Engine (Machine Learning):** Utilizes a Random Forest Classifier to analyze student metrics (CGPA, Aptitude, Technical Skills, Internships) and predict alignment with real-world job roles.
* **Multimodal AI Trainer:** Features an interactive interview simulator using the browser's Web Speech API for real-time speech-to-text feedback and Google MediaPipe for facial landmark, eye contact, and posture confidence tracking.
* **Dynamic Resume Builder:** Generates ATS-optimized, beautifully structured PDF resumes instantly from a user-friendly form using the `FPDF` engine.
* **Live Notice Board:** Integrates with the Remotive API to dynamically fetch and stream real-time global software engineering and tech job openings.
* **Role-Based Access Control (RBAC):** Built with a unified user identity model separating Admin panels from Student dashboards smoothly.
* **Secure Payment Integration:** Implements a professional "Pro Tier" system powered by secure Razorpay Checkout overlay workflows.

---

## 🛠️ Technical Stack

| Component | Technology Used |
| :--- | :--- |
| **Backend Framework** | Python (Flask) |
| **Machine Learning** | Scikit-Learn, Pandas, NumPy, Joblib |
| **Computer Vision / NLP** | Google MediaPipe, Web Speech API |
| **Database Engine** | SQLite / SQLAlchemy |
| **Document Processing** | FPDF |
| **Frontend Layout** | HTML5, CSS3, JavaScript (ES6), Particles.js, Bootstrap |
| **Payment Gateway** | Razorpay API |

---

## 📂 Project Architecture

```text
PPSU_CAREER/
│
├── model/
│   ├── placement_data.csv       # Historical student training dataset
│   ├── train_model.py           # Core ML preprocessing and Random Forest training script
│   └── placement_model.pkl      # Serialized pre-trained model ("The Brain")
│
├── static/                      # CSS, custom JavaScript, and asset files
├── templates/                   # Jinja2 dynamic HTML interfaces
├── app.py                       # Main Flask Application & controller routing logic
├── requirements.txt             # Project library dependencies
└── README.md                    # Repository documentation
