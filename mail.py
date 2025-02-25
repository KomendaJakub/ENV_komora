from csv import DictWriter
from datetime import datetime
from email.message import EmailMessage
from confidential import EMAIL, PASSWORD, MAIL_SERVER
import smtplib


def mail(address, xs, ys, zs):
    try:
        with open("Export.csv", 'w') as file:
            fieldnames = ['time', 'measurement', 'set_temp']

            writer = DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for i in range(len(xs)):
                writer.writerow(
                    {'time': xs[i], 'measurement': ys[i], 'set_temp': zs[i]})
    except Exception as err:
        print(err)
# "Could not open the Export.csv file."
        return err

    now = datetime.now()
    msg = EmailMessage()
    msg.set_content("Environmental chamber measurement from " +
                    now.strftime("%d/%m/%Y, %H:%M"))
    msg['Subject'] = "ENV chamber " + now.strftime("%d/%m/%Y, %H:%M")
    msg['From'] = EMAIL
    msg['To'] = address

    try:
        with open('Export.csv', 'rb') as fb:
            data = fb.read()
        msg.add_attachment(data, maintype='text',
                           subtype='csv', filename='Raw.csv')

#        plt.savefig('figure.png', dpi=1200)
        with open('figure.png', 'rb') as fb:
            image = fb.read()
        msg.add_attachment(image, maintype='image',
                           subtype='png', filename='Figure.png')

        with open('profile.csv', 'rb') as fb:
            prof = fb.read()
        msg.add_attachment(prof, maintype="text",
                           subtype="csv", filename="profile.csv")

    except Exception as err:
        print(err)
        return err
    try:
        with smtplib.SMTP_SSL(MAIL_SERVER, 465) as smtp:
            smtp.login(EMAIL, PASSWORD)
            smtp.send_message(msg)
    except Exception as err:
        print(err)
#        status.config(
#            text="There was an error while sending the email, try again or save manually!", bg="red")
#        root.after(30000, clear_status)
        return err

#    status.config(text="Email sent successfully!", bg="green")
#    root.after(10000, clear_status)
    return 0
