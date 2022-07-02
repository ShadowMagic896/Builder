import os


def main():

    with open("logs/format.log", "w") as log:
        print("\n--- FORMATTING [BLACK] ---\n", file=log)
    os.system("py -m black -v logs/format.log 2>> logs/format.log")

    with open("logs/format.log", "a") as log:
        print("\n--- FORMATTING [IMPORT] ---\n", file=log)
    os.system("py -m importanize -v . 2>> logs/format.log")

if __name__ == "__main__":
    main()
