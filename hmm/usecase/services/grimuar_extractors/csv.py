import asyncio
import csv
import io
from fastapi import UploadFile
from loguru import logger

from hmm.core.exceptions import BadCsvFileError
from hmm.enum import SubTaskType
from hmm.schemas.tasks.subtask_tasks import TypicalSubTaskCreate


def _reader(in_file: UploadFile) -> io.StringIO:
    return io.StringIO(in_file.file.read().decode())


class CSVGrimuarExtractor:

    _mapper: dict[str, str] = {
        "Типовая работа": "name",
        "Тип изменения": "task_type",
        "Уровень сложности": "task_lvl",
        "Стратегия ": "s_mana",
        "Магия": "m_mana",
        "Бой": "w_mana",
    }

    def __init__(self, data: list[TypicalSubTaskCreate]):
        self.data = data

    @classmethod
    async def from_body(cls, in_file: UploadFile):
        try:
            reader = csv.DictReader(await asyncio.to_thread(_reader, in_file))
            res = await asyncio.to_thread(cls.extract, reader)
            return cls(res)
        except Exception as e:
            logger.error("{}", e)
            raise BadCsvFileError() from e

    @classmethod
    def extract(cls, reader: csv.DictReader) -> list[TypicalSubTaskCreate]:
        tlvl_map = {"простой": 1, "средний": 2, "сложный": 3}
        res = []
        ire = iter(reader)
        for raw in ire:
            tdata = {
                cls._mapper[rki]: rvi
                for rki, rvi in raw.items()
                if rki in cls._mapper
            }
            tdata["task_type"] = (
                SubTaskType.creation
                if tdata["task_type"].strip().lower() == "создание"
                else SubTaskType.updation
            )
            tdata["task_lvl"] = tlvl_map[tdata["task_lvl"].strip().lower()]
            logger.debug("{}\n{}", raw, tdata)
            tdata["w_mana"] = float(tdata["w_mana"].replace(",", "."))
            tdata["m_mana"] = float(tdata["m_mana"].replace(",", "."))
            tdata["s_mana"] = float(tdata["s_mana"].replace(",", "."))
            res.append(TypicalSubTaskCreate(**tdata))
        return res
