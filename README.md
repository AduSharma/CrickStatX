CrickStatX is a cricket analytics dashboard that provides insights, comparisons, and performance data for international cricket players.

#Features 
- Search players with live suggestions  
- View player profile: batting, bowling, fielding stats  
- Analyze performance and trends  
- Display format/role tags  
- Export views and data as PDF  
- Smooth UI animations and transitions  

# 🛠 Tech Stack
| Component | Technology |
|-----------|------------|
| Frontend  | Svelte |
| Backend   | FastAPI (Python) |
| Data      | Kaggle datasets, pandas |
| Export    | jsPDF + html2canvas |
| Hosting   | Netlify / Render |

1. Clone the repo  
   git clone https://github.com/AduSharma/CrickStatX.git
   
2. Setup backend
cd CrickStatX/backend
pip install -r requirements.txt
uvicorn main:app --reload
3. Setup frontend
cd ../frontend
npm install
npm run dev
4. Open browser at http://localhost:5173 (or your configured port)

# Project Structure
CrickStatX/
├── backend/        # FastAPI server and data logic  
├── frontend/       # Svelte app  
├── datasets/       # Raw CSVs & data files  
└── README.md       # Project documentation  



