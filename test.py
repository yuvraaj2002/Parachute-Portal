import bcrypt

# Your new password
password = b"12345678"

# Generate a salt and hash the password
salt = bcrypt.gensalt(rounds=12)  # 12 is the cost factor, same as your example
hashed = bcrypt.hashpw(password, salt)

print(hashed.decode())  # This is your new bcrypt hash
