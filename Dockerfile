# Copyright 2023 Amazon.com and its affiliates; all rights reserved. This file is Amazon Web Services Content and may not be duplicated or distributed without permission.

FROM python:3.9 
# Or any preferred Python version.
ADD *.py ./
ADD root-ca.pem ./
ADD sample_data/*.csv ./
ADD *.pickle ./
COPY requirements.txt /tmp/requirements.txt
EXPOSE 5001
RUN python3 -m pip install -r /tmp/requirements.txt
CMD python3 -m flask_app ./graph_100kEdges_10kNodes.csv
# Or enter the name of your unique directory and parameter set.