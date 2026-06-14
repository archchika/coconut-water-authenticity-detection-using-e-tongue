"""
Run ML model manually: input pH and temperature, output citric acid and ascorbic acid %.
Usage:
  python ML_1/run_predict.py              # prompts for input
  python ML_1/run_predict.py 3.5 25       # pH=3.5, temp=25
"""
import sys

try:
    from predict import predict
except ImportError:
    from ML_1.predict import predict


def main() -> None:
    if len(sys.argv) >= 3:
        ph = float(sys.argv[1])
        temp = float(sys.argv[2])
    else:
        print("ML Model — pH + Temperature → Citric acid %, Ascorbic acid %")
        print("-" * 50)
        ph = float(input("Enter pH: "))
        temp = float(input("Enter temperature (°C): "))

    result = predict(pH=ph, temperature=temp)
    print()
    print("Output:")
    print(f"  Citric acid:   {result['citric_percent_wv']:.4f}%")
    print(f"  Ascorbic acid: {result['ascorbic_percent_wv']:.4f}%")


if __name__ == "__main__":
    main()
