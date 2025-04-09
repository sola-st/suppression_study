FROM python:3.10-slim

WORKDIR /suppression_home

# Install system dependencies (optional: update pip + install build deps)
RUN apt-get update && apt-get install -y \
    git \
    && pip install --upgrade pip

RUN apt-get install sloccount

COPY . /suppression_home

# Install dependencies
RUN pip install -r requirements.txt

RUN pip install -e .

CMD ["/bin/bash"]
