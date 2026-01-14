"""
Generate test password hashes
"""
import hashlib
import bcrypt


def md5_hash(text: str) -> str:
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def bcrypt_hash(text: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(text.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        print(f"Verify error: {e}")
        return False


# Test data
test_password = "123456"
test_phone = "13261276633"

print("=" * 70)
print("Password Generation Tool")
print("=" * 70)
print(f"\nOriginal password: {test_password}")
print(f"Phone: {test_phone}\n")

# Frontend MD5
md5_password = md5_hash(test_password)
print(f"1. Frontend MD5 (what frontend sends): {md5_password}")

# Database bcrypt (original password - WRONG approach)
bcrypt_original = bcrypt_hash(test_password)
print(f"2. Database bcrypt of original password: {bcrypt_original}")

# Database bcrypt (MD5 password - CORRECT approach)
bcrypt_md5 = bcrypt_hash(md5_password)
print(f"3. Database bcrypt of MD5 password: {bcrypt_md5}")

print("\n" + "=" * 70)
print("Verification Tests:")
print("=" * 70)

# Test 1: Verify MD5 password against bcrypt of MD5 (CORRECT)
result1 = verify_password(md5_password, bcrypt_md5)
print(f"\n[Method 1 - CORRECT]")
print(f"  MD5 password: {md5_password}")
print(f"  Bcrypt hash:  {bcrypt_md5}")
print(f"  Result: {result1}")

# Test 2: Verify original password against bcrypt of original (WRONG)
result2 = verify_password(test_password, bcrypt_original)
print(f"\n[Method 2 - WRONG for current implementation]")
print(f"  Original password: {test_password}")
print(f"  Bcrypt hash:       {bcrypt_original}")
print(f"  Result: {result2}")

# Test 3: Verify MD5 password against bcrypt of original (CURRENT PROBLEM)
result3 = verify_password(md5_password, bcrypt_original)
print(f"\n[Method 3 - CURRENT PROBLEM]")
print(f"  MD5 password:      {md5_password}")
print(f"  Bcrypt of original: {bcrypt_original}")
print(f"  Result: {result3}")

print("\n" + "=" * 70)
print("SQL Statements:")
print("=" * 70)

print(f"""
-- CORRECT: Store MD5 password's bcrypt hash
UPDATE users
SET password_hash = '{bcrypt_md5}',
    updated_at = NOW()
WHERE phone = '{test_phone}';
""")

print("\nNOTE:")
print("- Frontend sends MD5 hash of password")
print("- Database should store bcrypt hash of MD5 password")
print("- This way verify_password(MD5_password, bcrypt_hash) works correctly")
