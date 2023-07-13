DSN=$1

psql $DSN <<EOF
CREATE TABLE IF NOT EXISTS widgets (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS widgets_api_users (
    username TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    password_salt TEXT UNIQUE NOT NULL
);

-- the password_hash inserted below is the sha512 of "test_user_password" with
-- the salt "123456789" concatenated to it on the end
INSERT INTO widgets_api_users
     VALUES ('test_user', '5f4cd2bc173017aa4c4a176c2a3083e9e211127ef60ff622e8c6d32965eecb55671d4d06e0d43ab06c622b987b24a2cf10b2191d166d4adfda0b49c693df0a6e', '123456789');
EOF