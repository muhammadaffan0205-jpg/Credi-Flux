# crediflux/core/db_connection.py
import mysql.connector
from mysql.connector import Error
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

_connection = None

def get_db():
    global _connection
    if _connection is None or not _connection.is_connected():
        try:
            _connection = mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                autocommit=False,
                connection_timeout=10,
            )
        except Error as e:
            raise ConnectionError(
                f"Cannot connect to MySQL ({DB_HOST}/{DB_NAME}): {e}\n"
                f"Check config.py credentials and that MySQL is running."
            )
    cursor = _connection.cursor(dictionary=True)
    return _connection, cursor

def close_db():
    global _connection
    if _connection and _connection.is_connected():
        _connection.close()
        _connection = None

def init_schema():
    conn, cur = get_db()
    statements = [
        # users table
        """
        CREATE TABLE IF NOT EXISTS users (
            id              INT AUTO_INCREMENT PRIMARY KEY,
            full_name       VARCHAR(120)        NOT NULL,
            username        VARCHAR(80)         NOT NULL UNIQUE,
            phone           VARCHAR(20)         NOT NULL UNIQUE,
            password        VARCHAR(255)        NOT NULL,
            easypaisa_num   VARCHAR(20)         DEFAULT NULL,
            wallet_balance  DECIMAL(12,2)       DEFAULT 0.00,
            created_at      TIMESTAMP           DEFAULT CURRENT_TIMESTAMP
        )
        """,
        # groups table (note: name 'groupss' to avoid keyword)
        """
        CREATE TABLE IF NOT EXISTS groupss (
            group_id    INT AUTO_INCREMENT PRIMARY KEY,
            group_name  VARCHAR(120)    NOT NULL,
            created_by  INT             NOT NULL,
            created_at  TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        # group_members (registered users)
        """
        CREATE TABLE IF NOT EXISTS group_members (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            group_id    INT NOT NULL,
            user_id     INT NOT NULL,
            joined_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uniq_member (group_id, user_id),
            FOREIGN KEY (group_id) REFERENCES groupss(group_id) ON DELETE CASCADE,
            FOREIGN KEY (user_id)  REFERENCES users(id)         ON DELETE CASCADE
        )
        """,
        # group_people (display names, may be guests)
        """
        CREATE TABLE IF NOT EXISTS group_people (
            person_id    INT AUTO_INCREMENT PRIMARY KEY,
            group_id     INT          NOT NULL,
            user_id      INT          NULL,
            display_name VARCHAR(120) NOT NULL,
            UNIQUE KEY uniq_group_name (group_id, display_name),
            FOREIGN KEY (group_id) REFERENCES groupss(group_id) ON DELETE CASCADE
        )
        """,
        # expenses
        """
        CREATE TABLE IF NOT EXISTS manual_expenses (
            expense_id   INT AUTO_INCREMENT PRIMARY KEY,
            group_id     INT             NOT NULL,
            description  VARCHAR(255)    NOT NULL,
            total_amount DECIMAL(10,2)   NOT NULL,
            created_at   TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES groupss(group_id) ON DELETE CASCADE
        )
        """,
        # expense shares
        """
        CREATE TABLE IF NOT EXISTS manual_expense_shares (
            share_id     INT AUTO_INCREMENT PRIMARY KEY,
            expense_id   INT             NOT NULL,
            person_id    INT             NOT NULL,
            paid_amount  DECIMAL(10,2)   NOT NULL DEFAULT 0,
            owed_amount  DECIMAL(10,2)   NOT NULL DEFAULT 0,
            FOREIGN KEY (expense_id) REFERENCES manual_expenses(expense_id) ON DELETE CASCADE,
            FOREIGN KEY (person_id)  REFERENCES group_people(person_id)     ON DELETE CASCADE
        )
        """,
        # settlements (optimised payments)
        """
        CREATE TABLE IF NOT EXISTS settlements (
            settlement_id   INT AUTO_INCREMENT PRIMARY KEY,
            group_id        INT             NOT NULL,
            debtor_name     VARCHAR(120)    NOT NULL,
            creditor_name   VARCHAR(120)    NOT NULL,
            amount          DECIMAL(10,2)   NOT NULL,
            is_paid         TINYINT(1)      DEFAULT 0,
            paid_at         TIMESTAMP       NULL,
            created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES groupss(group_id) ON DELETE CASCADE
        )
        """,
        # transactions (history)
        """
        CREATE TABLE IF NOT EXISTS transactions (
            txn_id          INT AUTO_INCREMENT PRIMARY KEY,
            user_id         INT             NOT NULL,
            group_id        INT             NULL,
            description     VARCHAR(255)    NOT NULL,
            amount          DECIMAL(10,2)   NOT NULL,
            paid_to         VARCHAR(120)    NOT NULL,
            txn_date        TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        # direct user debts (peer-to-peer)
        """
        CREATE TABLE IF NOT EXISTS user_debts (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            from_user_id INT NOT NULL,
            to_user_id   INT NOT NULL,
            amount       DECIMAL(10,2) NOT NULL,
            status       ENUM('pending','accepted','rejected','paid') DEFAULT 'pending',
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            accepted_at  TIMESTAMP NULL,
            paid_at      TIMESTAMP NULL,
            FOREIGN KEY (from_user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (to_user_id)   REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        # payment confirmations
        """
        CREATE TABLE IF NOT EXISTS payment_confirmations (
            id              INT AUTO_INCREMENT PRIMARY KEY,
            debtor_id       INT NOT NULL,
            creditor_id     INT NOT NULL,
            amount          DECIMAL(10,2) NOT NULL,
            settlement_id   INT NULL,
            direct_debt_id  INT NULL,
            status          ENUM('pending','confirmed','rejected') DEFAULT 'pending',
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            confirmed_at    TIMESTAMP NULL,
            FOREIGN KEY (debtor_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (creditor_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
    ]
    for sql in statements:
        cur.execute(sql)
    conn.commit()
    cur.close()
