FROM python:3.12.3
WORKDIR /app

#Copy the distribution pacakge
COPY dist/ds-service-1.tar.gz .

#Install the distribution package
RUN pip install --no-cache-dir ds-service-1.tar.gz

#Set the environment variable from flask app
ENV FLASK_APP=src/app/__init__.py

#EXPOSE the port
EXPOSE 8010

#Start the Flask app
CMD ["flask","run","--host=0.0.0.0","--port=8010"]
