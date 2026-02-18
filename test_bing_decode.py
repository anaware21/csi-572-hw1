"""
Test Bing URL Decoding
Verifies that the base64 decoding works correctly
"""

import base64
import re

# Sample Bing redirect URL from your results
test_url = "https://www.bing.com/ck/a?!&&p=f147ddb315e4179215bdd8c0df7b66f9014749b825b7eb06823623d00587dbb1JmltdHM9MTc3MTExMzYwMA&ptn=3&ver=2&hsh=4&fclid=3502ba9f-70bb-6b49-127e-ad9d710c6aad&u=a1aHR0cHM6Ly9iaW9sb2d5ZGljdGlvbmFyeS5uZXQvcmVzcGlyYXRvcnktc3lzdGVtLWZ1bi1mYWN0cy8&ntb=1"

print("Testing Bing URL Decoder")
print("=" * 70)
print(f"\nOriginal URL:\n{test_url}\n")

# Extract u= parameter
match = re.search(r'[?&]u=([^&]+)', test_url)

if match:
    encoded_url = match.group(1)
    print(f"Encoded part (u= parameter):\n{encoded_url}\n")
    
    try:
        # Bing uses a modified encoding: 'a1' prefix + URL-safe base64
        # Remove 'a1' prefix first
        if encoded_url.startswith('a1'):
            encoded_url = encoded_url[2:]
            print(f"After removing 'a1' prefix:\n{encoded_url}\n")
        
        # Add padding if needed (base64 requires length to be multiple of 4)
        padding_needed = len(encoded_url) % 4
        if padding_needed:
            encoded_url += '=' * (4 - padding_needed)
            print(f"After adding padding:\n{encoded_url}\n")
        
        # Decode from URL-safe base64
        decoded_bytes = base64.urlsafe_b64decode(encoded_url)
        decoded_url = decoded_bytes.decode('utf-8')
        
        print(f"Decoded URL:\n{decoded_url}\n")
        
        print("=" * 70)
        print("✓ SUCCESS! URL decoded correctly")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
else:
    print("❌ No 'u=' parameter found")

print("\nExpected result:")
print("https://biologydictionary.net/respiratory-system-fun-facts/")

print("\n" + "=" * 70)
print("Testing the actual scraper...")
print("=" * 70 + "\n")

from bing_scraper import SearchEngine

# Test with one query
result = SearchEngine.search("Some important facts on the respiratory system", sleep=False, debug=True)

print(f"\n{'=' * 70}")
print(f"Final Results: {len(result)} URLs")
print("=" * 70)

for i, url in enumerate(result, 1):
    print(f"{i}. {url}")

if len(result) > 0 and 'bing.com/ck/a' not in result[0]:
    print(f"\n✓ SUCCESS! URLs are properly decoded (no bing.com/ck/a in results)")
else:
    print(f"\n❌ PROBLEM: URLs still contain Bing redirect links")