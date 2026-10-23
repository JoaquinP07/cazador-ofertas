# Cazador de ofertas

Revisa cada 10 minutos las secciones de tecnología y electrodomésticos de varias tiendas uruguayas y avisa por Telegram cuando un producto baja de golpe (posible error de precio).

## Tiendas

| Tienda | Cobertura |
|---|---|
| ZonaTecno | Todo tecnología (~1.900 productos) |
| AMV Store | Tecnología y electrodomésticos (~1.700) |
| Tienda Soy Santander | Electro, tecnología, gaming, TV (~1.800) |
| Cover Company | Catálogo completo (~3.800) |
| Multiahorro / Tata | Electrodomésticos y electrónica (~440) |
| Devoto | Solo los 12 primeros de cada categoría (la web no deja ver más sin navegador) |
| Tienda Inglesa | ❌ bloquea las conexiones desde GitHub |
| Mercado Libre | ❌ bloquea las conexiones desde GitHub |

## Cuándo avisa

- Un producto cuesta **40% menos o más** que su precio habitual (la mediana de los últimos precios vistos).
- Un producto nuevo aparece con **60% o más** de descuento sobre su precio de lista.
- No repite el aviso del mismo producto durante 12 horas.

Los porcentajes se cambian en `cazador/nucleo.py`.

## Configuración

En **Settings → Secrets and variables → Actions** del repositorio:

- `TELEGRAM_TOKEN`: el token que da @BotFather.
- `TELEGRAM_CHAT_ID`: tu número de chat (te lo da @userinfobot).

Para una revisión de prueba: pestaña **Actions → Cazador de ofertas → Run workflow**, marcando "Revisión de prueba".
