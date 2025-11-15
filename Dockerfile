FROM registry.access.redhat.com/ubi9/python-311

USER root
RUN dnf install -y gcc gcc-c++ postgresql-devel && dnf clean all

USER 1001

WORKDIR /opt/app-root/src

COPY --chown=1001:0 requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=1001:0 . .

RUN python manage.py collectstatic --noinput

EXPOSE 8080

CMD ["gunicorn", "backend.wsgi:application", "--bind", "0.0.0.0:8080", "--workers", "4", "--timeout", "120"]
