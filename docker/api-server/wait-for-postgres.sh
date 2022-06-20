#!/bin/bash
# wait-for-postgres.sh

set -e
cmd="$@"

until PGPASSWORD=postgres psql -h "db" -U "postgres" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done


# Prepare variables
TABLE=api_server_user
SQL_EXISTS=$(printf '\dt "%s"' "$TABLE")

# Credentials
USERNAME=postgres
PASSWORD=postgres
DATABASE=edgeai

echo "Checking if table <$TABLE> exists ..."

# Check if table exists

# using #!/bin/bash
if [[ $(PGPASSWORD="$PASSWORD" psql -h "db" -U $USERNAME -d $DATABASE -c "$SQL_EXISTS") ]]
then
    echo "Table exists ..."

else
    echo "Table not exists ..., init database"
    # psql -U postgres -d edgeai < /tmp/edgeai.sql
    python3 manage.py makemigrations api_server
    python3 manage.py migrate
    echo "from api_server.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'admin123')" | python3 manage.py shell
fi


>&2 echo "Postgres is up - executing command"
exec $cmd