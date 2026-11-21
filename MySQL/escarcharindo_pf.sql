
-- ==========================================
-- PROYECTO: ESCARCHARINDO
-- BASE DE DATOS DEL SIMULADOR
-- ==========================================

CREATE DATABASE IF NOT EXISTS escarcharindo_simulador;

USE escarcharindo_simulador;

-- 1. CLIENTES
CREATE TABLE clientes (
    id_cliente INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    tipo_cliente VARCHAR(50),
    telefono VARCHAR(20),
    correo VARCHAR(120),
    direccion VARCHAR(200),
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. PRODUCTOS
CREATE TABLE productos (
    id_producto INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    presentacion VARCHAR(50),
    capacidad_ml INT,
    precio_venta DECIMAL(10,2) NOT NULL,
    costo_produccion DECIMAL(10,2)
);

-- 3. PEDIDOS
CREATE TABLE pedidos (
    id_pedido INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente INT NOT NULL,
    fecha_pedido DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_entrega DATE,
    estado VARCHAR(30) DEFAULT 'Pendiente',
    prioridad VARCHAR(20) DEFAULT 'Normal',
    total DECIMAL(12,2) DEFAULT 0,
    observaciones TEXT,

    FOREIGN KEY (id_cliente)
        REFERENCES clientes(id_cliente)
);

-- 4. DETALLE DE PEDIDOS
CREATE TABLE detalle_pedido (
    id_detalle INT AUTO_INCREMENT PRIMARY KEY,
    id_pedido INT NOT NULL,
    id_producto INT NOT NULL,
    cantidad INT NOT NULL,
    precio_unitario DECIMAL(10,2) NOT NULL,

    FOREIGN KEY (id_pedido)
        REFERENCES pedidos(id_pedido),

    FOREIGN KEY (id_producto)
        REFERENCES productos(id_producto)
);

-- 5. INSUMOS
CREATE TABLE insumos (
    id_insumo INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    unidad_medida VARCHAR(20) NOT NULL,
    stock_actual DECIMAL(12,2) DEFAULT 0,
    stock_minimo DECIMAL(12,2) DEFAULT 0,
    costo_unitario DECIMAL(10,2) DEFAULT 0
);

-- 6. LOTES DE PRODUCCION
CREATE TABLE produccion_lotes (
    id_lote INT AUTO_INCREMENT PRIMARY KEY,
    fecha_produccion DATE NOT NULL,
    volumen_litros DECIMAL(12,2) NOT NULL,
    tiempo_coccion_min INT,
    responsable VARCHAR(120),
    estado VARCHAR(30) DEFAULT 'En proceso'
);

-- 7. CONSUMO DE INSUMOS
CREATE TABLE consumo_insumos (
    id_consumo INT AUTO_INCREMENT PRIMARY KEY,
    id_lote INT NOT NULL,
    id_insumo INT NOT NULL,
    cantidad_utilizada DECIMAL(12,2) NOT NULL,

    FOREIGN KEY (id_lote)
        REFERENCES produccion_lotes(id_lote),

    FOREIGN KEY (id_insumo)
        REFERENCES insumos(id_insumo)
);

-- 8. CONTROL DE MERMAS
CREATE TABLE control_mermas (
    id_merma INT AUTO_INCREMENT PRIMARY KEY,
    id_lote INT,
    id_insumo INT,
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    cantidad_perdida DECIMAL(12,2) NOT NULL,
    motivo VARCHAR(200),
    responsable VARCHAR(120),

    FOREIGN KEY (id_lote)
        REFERENCES produccion_lotes(id_lote),

    FOREIGN KEY (id_insumo)
        REFERENCES insumos(id_insumo)
);

use escarcharindo_simulador;

create table movimientos_inventario (
    id_movimiento int auto_increment primary key,
    id_insumo int not null,
    tipo_movimiento varchar(20) not null,
    cantidad decimal(10,2) not null,
    motivo varchar(255),
    fecha_movimiento datetime default current_timestamp,
    responsable varchar(100),

    foreign key (id_insumo)
        references insumos(id_insumo)
);



#AQUI INICIA EL DESMADRE XD
USE escarcharindo_simulador;

SHOW TABLES;

USE escarcharindo_simulador;

-- PRODUCTOS
INSERT INTO productos
(nombre, presentacion, capacidad_ml, precio_venta, costo_produccion)
VALUES
('Escarchado de tamarindo', 'Botella', 500, 50.93, 37.00);

-- INSUMOS
INSERT INTO insumos
(nombre, unidad_medida, stock_actual, stock_minimo, costo_unitario)
VALUES
('Tamarindo', 'kg', 500, 100, 35.00),
('Azucar', 'kg', 300, 50, 25.00),
('Chile', 'kg', 100, 20, 45.00),
('Bolsas', 'piezas', 5000, 1000, 0.80),
('Tapas', 'piezas', 5000, 1000, 0.50),
('Etiquetas', 'piezas', 5000, 1000, 0.30);

-- CONSULTAR INFORMACION
SELECT * FROM productos;

SELECT * FROM insumos;

use escarcharindo_simulador;

describe produccion_lotes;

describe consumo_insumos;

describe control_mermas;

describe productos;

use escarcharindo_simulador;

alter table produccion_lotes
add column id_producto int null after id_lote;

alter table produccion_lotes
add constraint fk_lote_producto
foreign key (id_producto)
references productos(id_producto);

select * from productos;

select * from produccion_lotes
order by id_lote desc;

select nombre, stock_actual
from insumos
order by nombre;

select
    p.id_lote,
    i.nombre as insumo,
    c.cantidad_utilizada,
    i.unidad_medida
from consumo_insumos c
inner join produccion_lotes p
    on c.id_lote = p.id_lote
inner join insumos i
    on c.id_insumo = i.id_insumo
order by p.id_lote, i.nombre;

select *
from produccion_lotes
where id_lote between 1 and 4;

start transaction;

-- devolver al inventario los materiales de los lotes 1 al 4
update insumos i
inner join (
    select id_insumo, sum(cantidad_utilizada) as total
    from consumo_insumos
    where id_lote between 1 and 4
    group by id_insumo
) c on i.id_insumo = c.id_insumo
set i.stock_actual = i.stock_actual + c.total
where i.id_insumo in (
    select distinct id_insumo
    from consumo_insumos
    where id_lote between 1 and 4
);

-- eliminar los consumos de los lotes 1 al 4
delete from consumo_insumos
where id_lote between 1 and 4;

-- eliminar los lotes de prueba
delete from produccion_lotes
where id_lote between 1 and 4;

commit;

-- eliminar los lotes de prueba
delete from produccion_lotes
where id_lote between 1 and 4;

commit;

rollback;

-- desactivar safe update temporalmente
set sql_safe_updates = 0;

start transaction;

-- recuperar los materiales de los lotes 1 al 4
update insumos i
inner join (
    select id_insumo, sum(cantidad_utilizada) as total
    from consumo_insumos
    where id_lote between 1 and 4
    group by id_insumo
) c on i.id_insumo = c.id_insumo
set i.stock_actual = i.stock_actual + c.total;

-- eliminar consumos anteriores
delete from consumo_insumos
where id_lote between 1 and 4;

-- eliminar lotes anteriores
delete from produccion_lotes
where id_lote between 1 and 4;

commit;

-- volver a activar safe update
set sql_safe_updates = 1;

select * from produccion_lotes;

select nombre, stock_actual
from insumos
order by nombre;

describe clientes;
describe pedidos;
describe detalle_pedido;

select * from pedidos
order by id_pedido desc;

select * from detalle_pedido
order by id_detalle desc;

describe pedidos;

describe detalle_pedido;

describe produccion_lotes;

alter table produccion_lotes
add column id_pedido int null;

alter table produccion_lotes
add constraint fk_lote_pedido
foreign key (id_pedido)
references pedidos(id_pedido);

describe produccion_lotes;

select
    id_lote,
    id_pedido,
    id_producto,
    fecha_produccion,
    volumen_litros,
    responsable,
    estado
from produccion_lotes
where id_lote = 6;


describe pedidos;


create table entregas (
    id_entrega int auto_increment primary key,
    id_pedido int not null,
    fecha_salida datetime default current_timestamp,
    responsable_entrega varchar(100) not null,
    recibido_por varchar(100),
    fecha_recepcion datetime,
    observaciones varchar(255),
    estado_entrega varchar(30) default 'En tránsito',

    foreign key (id_pedido)
    references pedidos(id_pedido)
);


-- PRODUCTOS
INSERT INTO productos
(nombre, presentacion, capacidad_ml, precio_venta, costo_produccion)
VALUES
('Escarchado tradicional', 'Botella 1/2 litro', 500, 60.00, 0.00),
('Escarchado fuego', 'Botella 1/2 litro', 500, 65.00, 0.00),
('Escarchado tradicional', 'Botella 1/4 litro', 250, 35.00, 0.00),
('Escarchado fuego', 'Botella 1/4 litro', 250, 35.00, 0.00),
('Escarchado tradicional', 'Botella 1 litro', 1000, 117.00, 0.00),
('Escarchado fuego', 'Botella 1 litro', 1000, 125.00, 0.00),
('Escarchado', 'Cubeta 5 kg', 0, 450.00, 0.00),
('Vaso escarchado', 'Vaso 100 g', 0, 32.00, 0.00),
('Chamoy', 'Botella 1 litro', 1000, 38.00, 0.00),
('Chamoy', 'Botella 1/2 litro', 500, 60.00, 0.00);


-- PRODUCTOS
INSERT INTO productos
(nombre, presentacion, capacidad_ml, precio_venta, costo_produccion)
VALUES

-- TAMARINDO
('Escarchado Tamarindo', 'Botella 1/4 litro', 250, 35.00, 0.00),
('Escarchado Tamarindo Fuego', 'Botella 1/4 litro', 250, 35.00, 0.00),
('Escarchado Tamarindo', 'Botella 1/2 litro', 500, 60.00, 0.00),
('Escarchado Tamarindo Fuego', 'Botella 1/2 litro', 500, 65.00, 0.00),
('Escarchado Tamarindo', 'Botella 1 litro', 1000, 117.00, 0.00),
('Escarchado Tamarindo Fuego', 'Botella 1 litro', 1000, 125.00, 0.00),

-- SANDIA
('Escarchado Sandía', 'Botella 1/4 litro', 250, 35.00, 0.00),
('Escarchado Sandía Fuego', 'Botella 1/4 litro', 250, 35.00, 0.00),
('Escarchado Sandía', 'Botella 1/2 litro', 500, 60.00, 0.00),
('Escarchado Sandía Fuego', 'Botella 1/2 litro', 500, 65.00, 0.00),
('Escarchado Sandía', 'Botella 1 litro', 1000, 117.00, 0.00),
('Escarchado Sandía Fuego', 'Botella 1 litro', 1000, 125.00, 0.00),

-- CEREZA
('Escarchado Cereza', 'Botella 1/4 litro', 250, 35.00, 0.00),
('Escarchado Cereza Fuego', 'Botella 1/4 litro', 250, 35.00, 0.00),
('Escarchado Cereza', 'Botella 1/2 litro', 500, 60.00, 0.00),
('Escarchado Cereza Fuego', 'Botella 1/2 litro', 500, 65.00, 0.00),
('Escarchado Cereza', 'Botella 1 litro', 1000, 117.00, 0.00),
('Escarchado Cereza Fuego', 'Botella 1 litro', 1000, 125.00, 0.00),

-- MANGO (SIN EDICION FUEGO)
('Escarchado Mango', 'Botella 1/4 litro', 250, 35.00, 0.00),
('Escarchado Mango', 'Botella 1/2 litro', 500, 60.00, 0.00),
('Escarchado Mango', 'Botella 1 litro', 1000, 117.00, 0.00),

-- OTROS PRODUCTOS
('Escarchado', 'Cubeta 5 kg', 0, 450.00, 0.00),
('Vaso escarchado', 'Vaso 100 g', 0, 32.00, 0.00),
('Chamoy', 'Botella 1 litro', 1000, 38.00, 0.00),
('Chamoy', 'Botella 1/2 litro', 500, 60.00, 0.00);

-- ELIMINAR PRODUCTOS ANTERIORES
DELETE FROM productos
WHERE
    (nombre = 'Escarchado tradicional')
    OR (nombre = 'Escarchado fuego')
    OR (nombre = 'Escarchado' AND presentacion = 'Cubeta 5 kg')
    OR (nombre = 'Vaso escarchado')
    OR (nombre = 'Chamoy');

SELECT
    l.id_lote,
    p.nombre AS producto,
    l.volumen_litros,
    i.nombre AS insumo,
    c.cantidad_utilizada,
    i.unidad_medida
FROM produccion_lotes l
INNER JOIN consumo_insumos c
    ON l.id_lote = c.id_lote
INNER JOIN insumos i
    ON c.id_insumo = i.id_insumo
INNER JOIN productos p
    ON l.id_producto = p.id_producto
ORDER BY l.id_lote;

SELECT *
FROM consumo_insumos
WHERE id_lote = 6;

SELECT
    id_insumo,
    nombre,
    unidad_medida,
    stock_actual
FROM insumos;

SELECT
    id_producto,
    nombre,
    presentacion,
    capacidad_ml,
    precio_venta
FROM productos
ORDER BY id_producto;


select
    id_lote,
    id_pedido,
    id_producto,
    fecha_produccion,
    volumen_litros,
    estado
from produccion_lotes
where id_pedido = 4;

select
    cl.id_lote,
    i.nombre as insumo,
    cl.cantidad,
    i.stock_actual
from consumo_insumos cl
inner join insumos i
    on cl.id_insumo = i.id_insumo
where cl.id_lote in (7, 8, 9, 10, 11)
order by cl.id_lote, i.nombre;

describe consumo_insumos;

select
    cl.id_lote,
    i.nombre as insumo,
    cl.cantidad_utilizada,
    i.stock_actual
from consumo_insumos cl
inner join insumos i
    on cl.id_insumo = i.id_insumo
where cl.id_lote in (7, 8, 9, 10, 11)
order by cl.id_lote, i.nombre;

select *
from control_mermas
where id_lote in (7, 8, 9, 10, 11);

select
    i.id_insumo,
    i.nombre as insumo,
    sum(ci.cantidad_utilizada) as cantidad_a_devolver,
    i.stock_actual
from consumo_insumos ci
inner join insumos i
    on ci.id_insumo = i.id_insumo
where ci.id_lote in (7, 8, 9, 10)
group by i.id_insumo, i.nombre, i.stock_actual
order by i.nombre;

start transaction;

-- devolver al inventario los consumos de los lotes duplicados
update insumos
set stock_actual = stock_actual +
    case id_insumo
        when 1 then 4.00
        when 2 then 2.00
        when 3 then 1.10
        when 4 then 53.50
        when 5 then 20.00
        else 0
    end
where id_insumo in (1, 2, 3, 4, 5);

-- eliminar los consumos de los lotes duplicados
delete from consumo_insumos
where id_lote in (7, 8, 9, 10);

-- eliminar los cuatro lotes duplicados
delete from produccion_lotes
where id_lote in (7, 8, 9, 10);

-- revisar los lotes que siguen registrados
select *
from produccion_lotes
where id_pedido = 4;

-- revisar las existencias recuperadas
select id_insumo, nombre, stock_actual
from insumos
order by id_insumo;

select id_lote, id_pedido, id_producto, volumen_litros, estado
from produccion_lotes
where id_pedido = 4;

commit;

select
    id_lote,
    id_pedido,
    id_producto,
    volumen_litros,
    estado
from produccion_lotes
where id_pedido = 5;

select
    ci.id_lote,
    i.nombre as insumo,
    ci.cantidad_utilizada,
    i.stock_actual
from consumo_insumos ci
inner join insumos i
    on ci.id_insumo = i.id_insumo
where ci.id_lote in (12, 13, 14)
order by ci.id_lote, i.nombre;

select *
from control_mermas
where id_lote in (12, 13, 14);

start transaction;

-- devolver el azúcar descontado por los lotes duplicados
update insumos
set stock_actual = stock_actual + 0.55
where id_insumo = 2;

-- eliminar los consumos de los lotes duplicados
delete from consumo_insumos
where id_lote in (12, 13);

-- eliminar los lotes duplicados
delete from produccion_lotes
where id_lote in (12, 13);

-- comprobar que solo quede el lote válido
select *
from produccion_lotes
where id_pedido = 5;

-- comprobar el inventario de azúcar
select id_insumo, nombre, stock_actual
from insumos
where id_insumo = 2;

select id_lote, id_pedido, volumen_litros, estado
from produccion_lotes
where id_pedido = 5;

select
    id_pedido,
    count(*) as total_lotes
from produccion_lotes
where id_pedido is not null
group by id_pedido
having count(*) > 1;

commit;

alter table produccion_lotes
add unique key uq_lote_por_pedido (id_pedido);

select id_pedido, count(*) as total_lotes
from produccion_lotes
where id_pedido = 6
group by id_pedido;

select
    nombre,
    cantidad_actual,
    unidad_medida
from insumos
order by nombre;