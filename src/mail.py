# Importing standard python libraries
from csv import DictWriter
from datetime import datetime
from email.message import EmailMessage
import smtplib
import json

CONFIG_PATH = "resources/confidential.json"


def mail(session, address=None):
    # Load confidential data from config file
    with open(CONFIG_PATH) as file:
        config = json.load(file)

    if address is None:
        address = config['EMAIL']

    # TODO: Rewrite mail to return something that can be assesed as success or failure
    # Write data that will be later attached to the email
    try:
        with open("data/export/data.csv", 'w') as file:
            # TODO: Change these fieldnames
            fieldnames = ['time', 'measurement', 'set_temp']

            writer = DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for time, real, target in zip(session.times, session.real_temps, session.target_temps):
                writer.writerow(
                    {'time': time, 'measurement': real, 'set_temp': target}
                )
    except Exception:
        return "Could not open export file. Please try to save manually."

    # Create the email message
    now = datetime.now()
    msg = EmailMessage()
    msg.set_content("Environmental chamber measurement from " +
                    now.strftime("%d/%m/%Y, %H:%M"))
    msg['Subject'] = "ENV chamber " + now.strftime("%d/%m/%Y, %H:%M")
    msg['From'] = config['EMAIL']
    msg['To'] = address

    # Add attachments to the email
    try:
        with open('data/export/data.csv', 'rb') as fb:
            data = fb.read()
        msg.add_attachment(data, maintype='text',
                           subtype='csv', filename='data.csv')

        with open('data/export/figure.png', 'rb') as fb:
            image = fb.read()
        msg.add_attachment(image, maintype='image',
                           subtype='png', filename='figure.png')

        with open('resources/templates/profile.csv', 'rb') as fb:
            prof = fb.read()
        msg.add_attachment(prof, maintype="text",
                           subtype="csv", filename="profile.csv")

    except Exception:
        return "Could not add attachments. Please try to save manually."

    # Connect to the mailing server and send the email
    try:
        with smtplib.SMTP_SSL(config['MAIL_SERVER'], 465) as smtp:
            smtp.login(config['EMAIL'], config['PASSWORD'])
            smtp.send_message(msg)
    except Exception:
        return "Error while connecting to the mailing server. Please try to save manually."

    return "ok"
