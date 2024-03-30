import sys
import argparse
import logging

def main():
    parser = argparse.ArgumentParser(description="Download and process files from a GitHub repository.")
    parser.add_argument("script", type=str, help="The script to run",
                        choices=["g2f", "gui", "ts-js-rust"],
                        default="g2f", nargs='?')
    args, remaining_args = parser.parse_known_args()
    logging.debug(f"Running {args.script} with arguments: {remaining_args}")

    if args.script == "gui":
        from github2file.gui import main as gui_main
        gui_main(remaining_args)
    elif args.script == "ts-js-rust":
        from github2file.ts_js_rust2file import main as ts_js_rust_main
        ts_js_rust_main(remaining_args)
    else:
        from github2file.github2file import main as g2f_main
        g2f_main(remaining_args)  # Pass all arguments after the 'g2f' token

if __name__ == "__main__":
    main()
