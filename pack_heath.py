"""packs heath files for delivery
usage: `python pack_heath.py -v x.y.z"""

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
        dirs = [
            target_dir,
            f"{target_dir}/UserObjects",
            f"{target_dir}/UserObjects/heath",
            f"{target_dir}/UserObjects/brimstone_data",
        ]

        for d in dirs:
            os.mkdir(d)

        files = {
            f"./README.md": f"{target_dir}/README.md",
            f"./dist/heathUI_{version}.gh": f"{target_dir}/heathUI_{version}.gh",
            f"./brimstone/brimstone.py": f"{target_dir}/UserObjects/brimstone.py",
            f"./src/heath.py": f"{target_dir}/UserObjects/heath/heath.py",
            f"./src/heath_ui.py": f"{target_dir}/UserObjects/heath/heath_ui.py",
            f"./icons/butterfly_heath.png": f"{target_dir}/UserObjects/heath/butterfly_heath.png",
            f"./src/patch_honeybee.py": f"{target_dir}/UserObjects/heath/patch_honeybee.py",
        }

        for f,t in files.items():
            shutil.copy(f, t)
            print(f"copied {f}")

        for file in os.listdir("./brimstone/brimstone_data"):
            shutil.copy(f"./brimstone/brimstone_data/{file}", f"{target_dir}/UserObjects/brimstone_data/{file}")
            print(f"copied {file}")

        shutil.make_archive(target_dir, "zip", target_dir)
        shutil.rmtree(target_dir)

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
