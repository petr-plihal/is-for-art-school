# Manuální setup pro vývoj

## Předpoklady

- Python, 3.10.12 byl použit
- MySQL server (nainstalovaný a spuštěný)


## Spuštění aplikace

1. Vytvořte a aktivujte virtuální prostředí pro Python.
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

2. Nainstalujte závislosti.
    ```bash
    pip install -r ../requirements.txt
    ```

3. Zprovozněte databázi pro aplikaci v MySQL.

    Přihlašte se do MySQL jako root:
    ```bash
    sudo mysql -u root -p
    ```

    Vytvořte databázi:
    ```sql
    CREATE DATABASE umelecka_skola_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_czech_ci;
    ```

    Vytvořte uživatele a nastavte mu heslo:
    ```sql
    CREATE USER 'dev_admin'@'localhost' IDENTIFIED BY 'dev_heslo';
    GRANT ALL PRIVILEGES ON umelecka_skola.* TO 'dev_admin'@'localhost';
    FLUSH PRIVILEGES;
    EXIT;
    ```

4. Spusťte vývojový server.
    ```bash
    flask run
    ```

    Server by měl běžet na localhostu (127.0.0.1) na portu 5000, jak je uvedeno ve výstupu.

    **Upozornění: Server slouží pro vývoj, běží lokálně a neobsahuje žádná nebo téměř žádná bezpečnostní opatření.**

5. Pro interakci s informačním systémem je třea založit účet, nebo se přihlásit na jeden z existujících:
    | Login    | Heslo | Role                    |
    | -------- | ----- | ----------------------- |
    | admin    | aaa   | Administrátor           |
    | spravce1 | aaa   | Správce ateliéru        |
    | vyucuj1  | aaa   | Vyučující               |
    | user1    | aaa   | Registrovaný uživatel   |
    |          |       | Neregistrovaný uživatel |

    Různé účty mají různá oprávnění k operacím, nebo zobrazování dat.

## Úklid po ukončení serveru

Pokud jste s vývojem skončili a neplánujete server dále používat, můžete odstranit vše, co bylo během nastavení vytvořeno.

1. Smažte databázi.
    ```bash
    sudo mysql -u root -p
    mysql> DROP DATABASE test;
    mysql> exit
    ```

2. Deaktivujte a odstraňte virtuální prostředí.
    ```bash
    deactivate  # pokud je venv aktivní
    rm -rf venv  # smaže venv obsahující balíčky