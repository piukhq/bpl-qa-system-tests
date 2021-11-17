from enum import Enum


class VoucherUpdateStatuses(Enum):
    ISSUED = "issued"
    CANCELLED = "cancelled"
    REDEEMED = "redeemed"


class FileAgentType(Enum):
    IMPORT = "import"
    UPDATE = "update"
