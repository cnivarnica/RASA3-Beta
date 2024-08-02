***********************************************************
cd rasa\app
rasa run --model ./models --enable-api --cors "*"
rasa train --domain .\domain
rasa interactive --domain ./domain
rasa shell
rasa test --domain .\domain
***********************************************************
cd frontend
python -m http.server 8000
***********************************************************
cd nlg_server
python nlg_server.py
***********************************************************
cd actions_server
python actions_server.py