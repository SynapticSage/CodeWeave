import argparse

def main():
    parser = argparse.ArgumentParser(description="Download and process files from a GitHub repository.")
    # parser.add_argument("script", type=str, help="The script to run",
    #                     choices=["g2f", "gui", "ts-js-rust"],
    #                     default="g2f", nargs='?')
    _, remaining_args = parser.parse_known_args()

    from github2file.g2f import main as g2f_main
    g2f_main(remaining_args)  # Pass all arguments after the 'g2f' token

if __name__ == "__main__":
    main()
