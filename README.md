# 🔍 Campus Lost & Found Portal

A modern, community-driven web application designed to help students and faculty reconnect with their lost belongings. Built with **Flask** and **Firebase**, this portal provides a real-time, persistent platform for reporting and claiming items.

---

## ✨ Features

* **Report Lost/Found Items**: Easy-to-use forms for reporting items with details like category, location, and date.
* **Image Hosting**: Integrated with **Firebase Storage** for persistent, cloud-based image management.
* **Real-time Database**: Powered by **Firestore** for instant updates and robust data handling.
* **Search & Filter**: Find items quickly by keywords, category, or item type (Lost vs. Found).
* **Claim System**: Users can submit claims for items, allowing owners to verify identity via a messaging system.
* **Responsive Design**: A modern, airy UI built with **Bootstrap 5** and **Lucide Icons** that looks great on mobile and desktop.
* **Easter Egg**: Includes a fun Python developer easter egg (`import antigravity`).

---

## 🛠️ Tech Stack

* **Backend**: Python / Flask
* **Database**: Google Firebase Firestore
* **Storage**: Google Firebase Storage
* **Frontend**: HTML5, Jinja2, CSS3 (Custom Airy Theme), Bootstrap 5
* **Icons**: Lucide-Static

---

## 🚀 Getting Started

### 1. Prerequisites
* Python 3.10 or higher
* A Google Firebase Project

### 2. Installation

1.  **Clone the repository**:
    ```bash
    git clone [https://github.com/your-username/campus-lost-found.git](https://github.com/your-username/campus-lost-found.git)
    cd campus-lost-found
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install flask firebase-admin werkzeug google-cloud-storage
    ```

### 3. Firebase Configuration

1.  Go to the [Firebase Console](https://console.firebase.google.com/).
2.  Generate a new **Private Key** for your service account:
    * Project Settings > Service accounts > Generate new private key.
3.  Rename the downloaded JSON file to `serviceAccount.json` and place it in the root directory.
4.  In the Firebase Console, enable **Firestore Database** and **Firebase Storage**.
5.  Set your Storage Rules to allow public reads for item images.

### 4. Running the App
```bash
python app.py
