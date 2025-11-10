from answer import answer
def main():
    print("=== Recipe Chat CLI ===")
    print("Type 'exit' to quit.\n")

    while True:
        try:
            user_input = input("User: ")
            if user_input.strip().lower() in ["exit", "quit"]:
                print("Bot: Goodbye!")
                break
            answer(user_input)
        except KeyboardInterrupt:
            print("\nBot: Exiting chat.")
            break


if __name__ == "__main__":
    main()
