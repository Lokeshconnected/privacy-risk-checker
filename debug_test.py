from utils import extract_text_from_image, analyze_privacy_risk

print("Import successful!")

# Check if the functions are defined and callable
print("Function extract_text_from_image is defined:", callable(extract_text_from_image))
print("Function analyze_privacy_risk is defined:", callable(analyze_privacy_risk))

# If we have a sample image, we can try to run the function, but without an API key it will fail.
# Instead, we can try to see if the function can be called with a dummy path and catch the error.

try:
    # This will fail because we don't have a valid image path and API key, but we can see if the function is called without import errors.
    # We are just checking if the function can be called without missing arguments.
    extract_text_from_image("dummy_path")
except Exception as e:
    print("Function extract_text_from_image called, but failed as expected:", e)

try:
    analyze_privacy_risk("dummy text")
except Exception as e:
    print("Function analyze_privacy_risk called, but failed as expected:", e)