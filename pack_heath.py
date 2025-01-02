"""packs heath files for delivery"""

import argparse
import os
import shutil

def main(args):
    version = args.version
    if not version:
        print("no version specified using -v, exiting")
        return
    target_dir = f"./dist/heath_{version}"
    try:
        os.mkdir(target_dir)
        shutil.copy(f"./README.md", f"{target_dir}/README.md")
        print(f"copied README.md")

        shutil.copy(f"./dist/heathUI_{version}.gh", f"{target_dir}/heathUI_{version}.gh")
        print(f"copied heathUI_{version}.gh")

        os.mkdir(f"{target_dir}/UserObjects")
        shutil.copy(f"./brimstone/brimstone.py", f"{target_dir}/UserObjects/brimstone.py")
        print(f"copied brimstone.py")

        os.mkdir(f"{target_dir}/UserObjects/heath")
        shutil.copy(f"./src/heath.py", f"{target_dir}/UserObjects/heath/heath.py")
        print(f"copied heath.py")

        os.mkdir(f"{target_dir}/UserObjects/brimstone_data")
        for file in os.listdir("./brimstone/brimstone_data"):
            print(f"copied {file}")
            shutil.copy(f"./brimstone/brimstone_data/{file}", f"{target_dir}/UserObjects/brimstone_data/{file}")

        shutil.make_archive(target_dir, "zip", target_dir)

    except:
        # it failed, remove the broken directory
        shutil.rmtree(target_dir)
        zip_file = f"{target_dir}.zip"
        if os.path.isfile(zip_file):
            os.remove(zip_file)
        raise


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-v", "--version", help="string representing the version")
    main(args = arg_parser.parse_args())
