from enum import IntEnum

from hmm.core.utils.common import EnumDescriptionMixin


class HeroCategory(EnumDescriptionMixin, IntEnum):
    warrior = 1
    magician = 2
    strategist = 3


class SubTaskType(EnumDescriptionMixin, IntEnum):
    creation = 1
    updation = 2
