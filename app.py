from flask import Flask, request, jsonify
from flask_cors import CORS  # ✅ Add this
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import spacy

app = Flask(__name__)
CORS(app)  # ✅ Enable CORS for all routes

# ✅ Load spaCy NLP model
nlp = spacy.load("en_core_web_sm")

# ✅ Google Sheets API setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("chatbot-creds.json", scope)
client = gspread.authorize(creds)

def load_sheet_data():
    sheet = client.open("EmployeeSupportBot").sheet1
    return sheet.get_all_records()

def extract_keywords(text):
    doc = nlp(text.lower())
    return [token.lemma_ for token in doc if not token.is_stop and token.is_alpha]

@app.route("/")
def index():
    return "✅ NLP Chatbot Backend is Running"

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "")
    if not user_msg:
        return jsonify({"reply": "❌ Please enter a message."}), 400

    qa_data = load_sheet_data()
    user_keywords = extract_keywords(user_msg)

    matched_answers = []

    for row in qa_data:
        keywords = row.get("Question", "").lower().split(",")
        for k in keywords:
            k = k.strip()
            if any(k in word for word in user_keywords):
                matched_answers.append(row.get("Answer"))
                break  # Avoid duplicates

    if matched_answers:
        if len(matched_answers) == 1:
            return jsonify({"reply": matched_answers[0]})
        else:
            reply = "🔎 I found a few answers related to your query:\n"
            for i, ans in enumerate(matched_answers, 1):
                reply += f"{i}. {ans}\n"
            return jsonify({"reply": reply.strip()})

    return jsonify({"reply": "❓ Sorry, I couldn't find anything related to that."})

if __name__ == "__main__":
    print("✅ Starting NLP-enhanced chatbot...")
    app.run(debug=True)
