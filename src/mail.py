# Importing standard python libraries
from csv import DictWriter
from datetime import datetime
from email.message import EmailMessage
import smtplib

# Importing config options
# TODO: Rewrite using json config file
from src.confidential import EMAIL, PASSWORD, MAIL_SERVER


def mail(session, address=EMAIL):
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
    except Exception as err:
        print(err)
# "Could not open the Export.csv file."
        return err

    # Create the email message
    now = datetime.now()
    msg = EmailMessage()
    msg.set_content("Environmental chamber measurement from " +
                    now.strftime("%d/%m/%Y, %H:%M"))
    msg['Subject'] = "ENV chamber " + now.strftime("%d/%m/%Y, %H:%M")
    msg['From'] = EMAIL
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

    except Exception as err:
        print(err)
        return err

    # Connect to the mailing server and send the email
    try:
        with smtplib.SMTP_SSL(MAIL_SERVER, 465) as smtp:
            smtp.login(EMAIL, PASSWORD)
            smtp.send_message(msg)
    except Exception as err:
        print(err)
        return err

    return 0
