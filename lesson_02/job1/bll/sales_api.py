from lesson_02.job1.dal import local_disk, sales_api


def save_sales_to_local_disk(date: str, raw_dir: str) -> None:
    """
    Download sales from API and store them locally.

    :param date: date to retrieve sales for
    :param raw_dir: path where to save sales
    """
    data = sales_api.get_sales(date)
    local_disk.save_to_disk(data, raw_dir)
