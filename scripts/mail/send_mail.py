import logging
import os
import smtplib
from email.message import EmailMessage

import requests

from base.models import Client

import my_project.settings as local
from scripts.utils.str_utils import check_valid_email

# Mailgun API key — set via the MAILGUN_API_KEY environment variable.
API_KEY = os.environ.get("MAILGUN_API_KEY", "")


def msg_service(subject, to, body, filepath=None, cc=None, reply_to="info@topocs.com.au"):
    try:
        data = {"from": "TOCS Info <postmaster@mg.topocs.com.au>",
                "to": [to, ],
                "subject": subject,
                "text": body,
                "h:Reply-To": reply_to
                }
        if cc:
            data ['cc'] = cc

        if filepath:
            filename = filepath.split("/")
            filename = filename [-1]

            response = requests.post(
                "https://api.mailgun.net/v3/mg.topocs.com.au/messages",
                files=[("attachment", (filename, open(filepath, "rb").read())),
                       ],
                auth=("api", API_KEY),
                data=data
            )

        else:
            response = requests.post(
                "https://api.mailgun.net/v3/mg.topocs.com.au/messages",
                auth=("api", API_KEY),
                data=data)
        # print(response)



    except Exception as e:
        logging.exception(e)
    finally:
        # print(response)
        return response
