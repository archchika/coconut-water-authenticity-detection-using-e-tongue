"""
Run sugar model manually.

Usage:
  python ML_2/run_predict.py
  python ML_2/run_predict.py 5.5 3500 25 20
"""
import sys

try:
    from predict import predict
except ImportError:
    from ML_2.predict import predict


def main() -> None:
    if len(sys.argv) >= 5:
        ph = float(sys.argv[1])
        tds = float(sys.argv[2])
        temp = float(sys.argv[3])
        turb = float(sys.argv[4])
    else:
        print("ML_2 — pH + TDS + Temperature + Turbidity → Sugar %")
        print("-" * 55)
        ph = float(input("Enter pH: "))
        tds = float(input("Enter TDS (mg/L): "))
        temp = float(input("Enter temperature (°C): "))
        turb = float(input("Enter turbidity (NTU): "))

    result = predict(pH=ph, tds=tds, temperature=temp, turbidity=turb)
    print()
    print("Output:")
    print(f"  Sugar: {result['sugar_pct']:.4f}%")


if __name__ == "__main__":
    main()
