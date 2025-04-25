

import os
import zipfile


def compress_folder(folder_path, include_folder=False, overwrite_mode=False):
    """
    压缩指定文件夹

    :param folder_path: 要压缩的文件夹路径
    :param include_folder: 是否包含文件夹本身
    :param overwrite_mode: 是否覆盖已存在的压缩文件
    :return: 压缩包路径，如果压缩失败则返回None
    """
    try:
        # 仅文件夹名称
        base_name = os.path.basename(folder_path)
        # 父目录路径
        parent_dir = os.path.dirname(folder_path)
        # 构造压缩包文件名称
        zip_path = os.path.join(parent_dir, base_name + '.zip')

        # 检查压缩包是否已存在
        if os.path.exists(zip_path):
            if not overwrite_mode:
                print(f"跳过已存在压缩包: {zip_path}")
                return None

        # 创建压缩文件
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if include_folder:
                # 包含文件夹本身
                arcname = base_name
            else:
                # 只包含文件夹内的文件
                arcname = ''

            # 递归遍历所有子目录，并压缩文件
            # 当前遍历的路径root，当前路径下的子文件夹dirs，当前路径下的文件files
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    # 构造要添加到压缩包的文件的完整路径
                    file_path = os.path.join(root, file)
                    # 把 folder_path 从 file_path 去除
                    relative_path = os.path.relpath(file_path, folder_path)
                    # 构造文件在压缩包中的完整路径
                    arcfile_path = os.path.join(arcname, relative_path)
                    zipf.write(file_path, arcfile_path)

        print(f"已成功压缩文件到: {zip_path}")
        return zip_path

    except Exception as e:
        print(f"压缩 {folder_path} 时出错：{e}")
        return None


def main():
    # 输入文件夹路径
    while True:
        path = input("压缩指定路径下的所有文件夹，请输入路径：\n").strip()
        if os.path.exists(path) and os.path.isdir(path):
            break
        else:
            print("路径不存在或不是文件夹，请重新输入。\n")

    # 选择压缩模式
    include_folder_input = input("是否包含文件夹本身？(y/N，直接回车默认为否)：").strip().lower()
    include_folder = include_folder_input == 'y'

    # 选择覆盖模式
    overwrite_mode_input = input("是否覆盖已存在压缩包？(y/N，直接回车默认为否)：").strip().lower()
    overwrite_mode = overwrite_mode_input == 'y'

    # 遍历目录确定需要压缩的文件夹
    folders = [os.path.join(path, d) for d in os.listdir(path)
               if os.path.isdir(os.path.join(path, d))]

    # 压缩每个文件夹
    for folder in folders:
        compress_folder(folder, include_folder, overwrite_mode)

    print("\n所有压缩已完成")


if __name__ == "__main__":
    main()

