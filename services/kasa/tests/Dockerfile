FROM azureks.azurecr.io/base/pybase:v1.3 as base

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

RUN pip install pytest pytest-azurepipelines pytest-cov

FROM base
WORKDIR /app

COPY . .

RUN chmod u+x tests.sh
CMD ["bash", "tests.sh"]