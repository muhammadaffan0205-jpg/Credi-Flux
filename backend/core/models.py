# backend/core/models.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    user_id:          int
    full_name:        str
    username:         str
    phone:            str
    password:         str
    salt:             str
    easypaisa_num:    Optional[str]  = None
    wallet_balance:   float          = 0.0
    created_at:       Optional[datetime] = None

    @property
    def display_name(self) -> str:
        return self.full_name or self.username

    @property
    def pay_number(self) -> str:
        return self.easypaisa_num or self.phone

@dataclass
class Group:
    group_id:    int
    group_name:  str
    created_by:  int
    created_at:  Optional[datetime] = None
    member_count: int = 0

@dataclass
class Person:
    person_id:    int
    group_id:     int
    display_name: str
    user_id:      Optional[int] = None

@dataclass
class Expense:
    expense_id:   int
    group_id:     int
    description:  str
    total_amount: float
    created_at:   Optional[datetime] = None

@dataclass
class Settlement:
    settlement_id:  int
    group_id:       int
    debtor_name:    str
    creditor_name:  str
    amount:         float
    is_paid:        bool = False
    paid_at:        Optional[datetime] = None
    created_at:     Optional[datetime] = None

@dataclass
class Transaction:
    txn_id:      int
    user_id:     int
    group_id:    Optional[int]
    description: str
    amount:      float
    paid_to:     str
    txn_date:    Optional[datetime] = None