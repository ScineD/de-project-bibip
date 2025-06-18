from decimal import Decimal
from datetime import datetime
from models import Car, CarFullInfo, CarStatus, Model, ModelSaleStats, Sale
from pathlib import Path


class CarService:
    def __init__(self, root_directory_path: str) -> None:
        self.root_directory_path = Path(root_directory_path)
        self.root_directory_path.mkdir(parents=True, exist_ok=True)

    # Задание 1. Сохранение автомобилей и моделей
    def add_model(self, model: Model) -> Model:
        model_file = self.root_directory_path / "models.txt"
        index_file = self.root_directory_path / "models_index.txt"

        model_file.touch(exist_ok=True)
        index_file.touch(exist_ok=True)

        with open(model_file, "r", encoding="utf-8") as f:
            line_number = sum(1 for _ in f)

        with open(model_file, "a", encoding="utf-8") as f:
            f.write(f"{model.id};{model.name};{model.brand}\n")

        with open(index_file, "a", encoding="utf-8") as f:
            f.write(f"{model.id};{line_number}\n")

        return model

    # Задание 1. Сохранение автомобилей и моделей
    def add_car(self, car: Car) -> Car:
        car_file_path = self.root_directory_path / "cars.txt"
        index_file_path = self.root_directory_path / "cars_index.txt"

        car_file_path.touch(exist_ok=True)
        index_file_path.touch(exist_ok=True)

        with open(car_file_path, "r", encoding="utf-8") as f:
            line_number = sum(1 for _ in f)

        # Пишем как CSV: vin;model;price;date_start;status
        with open(car_file_path, "a", encoding="utf-8") as f:
            f.write(f"{car.vin};{car.model};{car.price};{car.date_start};{car.status}\n")

        with open(index_file_path, "a", encoding="utf-8") as f:
            f.write(f"{car.vin};{line_number}\n")

        return car
    
     # Задание 2. Сохранение продаж.
    def sell_car(self, sale: Sale) -> Car:
        sales_path = self.root_directory_path / "sales.txt"
        sales_idx_path = self.root_directory_path / "sales_index.txt"
        cars_path = self.root_directory_path / "cars.txt"
        cars_idx_path = self.root_directory_path / "cars_index.txt"

        # создадим файлы
        sales_path.touch(exist_ok=True)
        sales_idx_path.touch(exist_ok=True)

        # считаем номер строки для новой продажи
        with open(sales_path, "r", encoding="utf-8") as f:
            line_num = sum(1 for _ in f)

        # сохраняем продажу как csv
        with open(sales_path, "a", encoding="utf-8") as f:
            f.write(f"{sale.sales_number};{sale.car_vin};{sale.sales_date.isoformat()};{sale.cost}\n")

        # обновим индекс 
        with open(sales_idx_path, "a", encoding="utf-8") as f:
            f.write(f"{sale.sales_number};{line_num}\n")

        # находим мащину
        with open(cars_idx_path, "r", encoding="utf-8") as f:
            car_index = {line.split(";")[0]: int(line.split(";")[1]) for line in f if line.strip()}

        if sale.car_vin not in car_index:
            raise ValueError("Такой машины нет")

        line_no = car_index[sale.car_vin]

        # читаем таблицу
        with open(cars_path, "r", encoding="utf-8") as f:
            cars = f.readlines()

        car_fields = cars[line_no].strip().split(";")
        if len(car_fields) < 5:
            raise ValueError("битая строка в cars.txt")

        # меняем статус на sold
        car_fields[4] = "sold"
        cars[line_no] = ";".join(car_fields) + "\n"

        # пишем всё обратно
        with open(cars_path, "w", encoding="utf-8") as f:
            f.writelines(cars)

        # вернём объект
        return Car(
            vin=car_fields[0],
            model=int(car_fields[1]),
            price=Decimal(car_fields[2]),
            date_start=datetime.fromisoformat(car_fields[3]),
            status=CarStatus.sold
        )
    
    # Задание 3. Доступные к продаже
    def get_cars(self, status: CarStatus) -> list[Car]:
        cars = []
        cars_txt = self.root_directory_path / "cars.txt"

        with open(cars_txt, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(";")
                if len(parts) != 5:
                    continue

                try:
                    car = Car(
                        vin=parts[0],
                        model=int(parts[1]),
                        price=Decimal(parts[2]),
                        date_start=datetime.fromisoformat(parts[3]),
                        status=parts[4]
                    )
                    if car.status == status:
                        cars.append(car)
                except Exception:
                    continue

        return cars


    # Задание 4. Детальная информация
    def get_car_info(self, vin: str) -> CarFullInfo | None:
        cars_txt = self.root_directory_path / "cars.txt"
        cars_idx = self.root_directory_path / "cars_index.txt"
        models_txt = self.root_directory_path / "models.txt"
        models_idx = self.root_directory_path / "models_index.txt"
        sales_txt = self.root_directory_path / "sales.txt"

        # 1. находим строку с машиной
        with open(cars_idx, "r", encoding="utf-8") as f:
            vin_map = {line.split(";")[0]: int(line.split(";")[1]) for line in f if line.strip()}

        if vin not in vin_map:
            return None

        with open(cars_txt, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i == vin_map[vin]:
                    vin_, model_id, price, date_start, status = line.strip().split(";")
                    break
            else:
                return None

        # 2. читаем модель
        with open(models_idx, "r", encoding="utf-8") as f:
            model_map = {line.split(";")[0]: int(line.split(";")[1]) for line in f if line.strip()}

        model_id_str = str(model_id)
        if model_id_str not in model_map:
            return None

        with open(models_txt, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i == model_map[model_id_str]:
                    _, name, brand = line.strip().split(";")
                    break
            else:
                return None

        # 3. если машина продана — ищем продажу
        sale_date = None
        sale_cost = None
        if status == "sold":
            with open(sales_txt, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split(";")
                    if len(parts) >= 4 and parts[1] == vin:
                        sale_date = parts[2]
                        sale_cost = parts[3]
                        break

        return CarFullInfo(
            vin=vin_,
            car_model_name=name,
            car_model_brand=brand,
            price=Decimal(price),
            date_start=datetime.fromisoformat(date_start),
            status=status,
            sales_date=datetime.fromisoformat(sale_date) if sale_date else None,
            sales_cost=Decimal(sale_cost) if sale_cost else None
        )
    

    # Задание 4. Обновление ключевого поля
    def update_vin(self, vin: str, new_vin: str) -> Car:
        cars_txt = self.root_directory_path / "cars.txt"
        cars_idx = self.root_directory_path / "cars_index.txt"

        # читаем индекс
        with open(cars_idx, "r", encoding="utf-8") as f:
            idx_lines = [line.strip().split(";") for line in f if line.strip()]
        vin_to_line = {v: int(n) for v, n in idx_lines}

        if vin not in vin_to_line:
            raise ValueError(f"VIN '{vin}' not found in index.")

        line_num = vin_to_line[vin]

        # читаем все строки, чтобы потом одну заменить
        with open(cars_txt, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if line_num >= len(lines):
            raise ValueError("Строка не найдена в файле.")

        parts = lines[line_num].strip().split(";")
        if len(parts) != 5:
            raise ValueError("битая строка")

        # обновляем vin
        parts[0] = new_vin
        lines[line_num] = ";".join(parts) + "\n"

        # переписываем весь файл
        with open(cars_txt, "w", encoding="utf-8") as f:
            f.writelines(lines)

        # обновляем индекс
        new_idx_lines = [
            [new_vin if v == vin else v, str(n)] for v, n in idx_lines
        ]
        new_idx_lines.sort(key=lambda x: x[0])

        with open(cars_idx, "w", encoding="utf-8") as f:
            for v, n in new_idx_lines:
                f.write(f"{v};{n}\n")

        # создаём Car и возвращаем
        return Car(
            vin=new_vin,
            model=int(parts[1]),
            price=Decimal(parts[2]),
            date_start=datetime.fromisoformat(parts[3]),
            status=parts[4]
        )
    
    # Задание 6. Удаление продажи
    def revert_sale(self, sales_number: str) -> Car:
        sales_txt = self.root_directory_path / "sales.txt"
        cars_txt = self.root_directory_path / "cars.txt"
        index_txt = self.root_directory_path / "cars_index.txt"

        # читаем все продажи
        with open(sales_txt, "r", encoding="utf-8") as f:
            sales = f.readlines()

        sale_found = False
        line_no = None
        car_vin = None

        for i, line in enumerate(sales):
            parts = line.strip().split(";")
            if len(parts) < 4:
                continue
            if parts[0] == sales_number and (len(parts) < 5 or parts[4] != "deleted"):
                sale_found = True
                line_no = i
                car_vin = parts[1]
                break

        if not sale_found:
            raise ValueError(f"Sale {sales_number} not found")

        # помечаем как удалённую
        if len(sales[line_no].strip().split(";")) == 4:
            sales[line_no] = sales[line_no].strip() + ";deleted\n"
        else:
            sales[line_no] = ";".join(sales[line_no].strip().split(";")[:4]) + ";deleted\n"

        with open(sales_txt, "w", encoding="utf-8") as f:
            f.writelines(sales)

        # обновляем статус машины на available
        with open(index_txt, "r", encoding="utf-8") as f:
            index = {line.split(";")[0]: int(line.split(";")[1]) for line in f if line.strip()}

        if car_vin not in index:
            raise ValueError(f"VIN {car_vin} not found in index")

        car_line = index[car_vin]
        with open(cars_txt, "r", encoding="utf-8") as f:
            cars = f.readlines()

        car_parts = cars[car_line].strip().split(";")
        if len(car_parts) != 5:
            raise ValueError("битая строка")
        car_parts[4] = "available"
        cars[car_line] = ";".join(car_parts) + "\n"

        with open(cars_txt, "w", encoding="utf-8") as f:
            f.writelines(cars)

        # вернуть обновлённый Car
        return Car(
            vin=car_parts[0],
            model=int(car_parts[1]),
            price=Decimal(car_parts[2]),
            date_start=datetime.fromisoformat(car_parts[3]),
            status=car_parts[4]
        )
    
    # Задание 7. Самые продаваемые модели
    def top_models_by_sales(self) -> list[ModelSaleStats]:
        from collections import defaultdict

        sales_path = self.root_directory_path / "sales.txt"
        cars_path = self.root_directory_path / "cars.txt"
        cars_index_path = self.root_directory_path / "cars_index.txt"
        models_path = self.root_directory_path / "models.txt"
        models_index_path = self.root_directory_path / "models_index.txt"

        # VIN -> строка в cars.txt
        with open(cars_index_path, "r", encoding="utf-8") as f:
            vin_to_line = {line.split(";")[0]: int(line.split(";")[1]) for line in f if line.strip()}

        # Собираем VIN → (model_id, price)
        vin_to_model_price = {}
        with open(cars_path, "r", encoding="utf-8") as f:
            cars = f.readlines()
            for vin, line_no in vin_to_line.items():
                parts = cars[line_no].strip().split(";")
                if len(parts) < 5:
                    continue
                vin_to_model_price[vin] = (int(parts[1]), float(parts[2]))

        # Считаем продажи
        model_sales = defaultdict(int)
        model_total_price = defaultdict(float)

        with open(sales_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(";")
                if len(parts) < 4:
                    continue
                if len(parts) >= 5 and parts[4] == "deleted":
                    continue
                vin = parts[1]
                if vin in vin_to_model_price:
                    model_id, price = vin_to_model_price[vin]
                    model_sales[model_id] += 1
                    model_total_price[model_id] += price

        # Топ-3 моделей по количеству продаж, потом по средней цене
        top_models = sorted(
            model_sales.items(),
            key=lambda x: (-x[1], -model_total_price[x[0]] / x[1])
        )[:3]

        # model_id → строка
        with open(models_index_path, "r", encoding="utf-8") as f:
            model_index = {int(line.split(";")[0]): int(line.split(";")[1]) for line in f if line.strip()}

        result = []
        with open(models_path, "r", encoding="utf-8") as f:
            models = f.readlines()
            for model_id, sales_count in top_models:
                if model_id not in model_index:
                    continue
                parts = models[model_index[model_id]].strip().split(";")
                if len(parts) < 3:
                    continue
                result.append(ModelSaleStats(
                    car_model_name=parts[1],
                    brand=parts[2],
                    sales_number=sales_count
                ))

        return result