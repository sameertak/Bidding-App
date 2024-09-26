
# Bidding App

A Django-based application designed to manage bidding for transporters and logistics services. The app facilitates transporter bid submissions, offer proposals, and bid acceptance workflows, integrating seamless data handling for destinations and vehicles.

## Features
- Transporter bid submissions
- Offer proposals and acceptance
- Token-based authentication for secure transporter interactions
- Detailed bid tracking and reporting

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/sameertak/Bidding-App.git
   ```
2. Navigate to the project directory:
   ```bash
   cd Bidding-App
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run database migrations:
   ```bash
   python manage.py migrate
   ```
5. Start the development server:
   ```bash
   python manage.py runserver
   ```

## Usage
- Access the app at `http://localhost:8000`
- Manage transporters, bids, and offers using the web interface.

## License
This project is licensed under the MIT License.
