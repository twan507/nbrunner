import data_processor
import inspect

print("Các function có sẵn trong data_processor:")
for name, obj in inspect.getmembers(data_processor):
    if inspect.isfunction(obj):
        print(f"  - {name}")

print("\nKiểm tra cụ thể save_to_excel:")
if hasattr(data_processor, "save_to_excel"):
    print("✅ save_to_excel có sẵn")
    print(f"   Signature: {inspect.signature(data_processor.save_to_excel)}")
else:
    print("❌ save_to_excel không tìm thấy")
