# SEO-контент-план: журнал фермы «Рунская»

Статей: **14**. Материалы ориентированы на информационные запросы вокруг продукции фермы — картофеля, мёда, яйца, птицы и натурального земледелия — и ведут читателя к заявке на сайте.
Частотность и конкуренция запросов здесь **не заявлены**: перед масштабированием кластеров проверьте их в Яндекс Wordstat, Яндекс Вебмастере и Google Search Console.

| № | Основной запрос | Заголовок | Раздел | URL |
|---:|---|---|---|---|
| 1 | как хранить картофель | Как хранить картофель с фермы, чтобы он долежал до весны | Картофель | [kartofel-hranenie](https://bestdeejay-design.github.io/fermaruna/articles/kartofel-hranenie/) |
| 2 | как выбрать картофель | Как выбрать хороший картофель: на что смотреть при покупке | Картофель | [kartofel-vybor](https://bestdeejay-design.github.io/fermaruna/articles/kartofel-vybor/) |
| 3 | как выбрать настоящий мёд | Как выбрать настоящий мёд: признаки зрелого мёда | Мёд и пчёлы | [med-vybor](https://bestdeejay-design.github.io/fermaruna/articles/med-vybor/) |
| 4 | как хранить мёд | Как хранить мёд в домашних условиях | Мёд и пчёлы | [med-hranenie](https://bestdeejay-design.github.io/fermaruna/articles/med-hranenie/) |
| 5 | как проверить свежесть яйца | Как проверить свежесть куриного яйца: три домашних способа | Яйцо и птица | [yayco-svezhest](https://bestdeejay-design.github.io/fermaruna/articles/yayco-svezhest/) |
| 6 | как хранить куриные яйца | Как хранить домашние яйца: срок, температура, холодильник | Яйцо и птица | [yayco-hranenie](https://bestdeejay-design.github.io/fermaruna/articles/yayco-hranenie/) |
| 7 | породы кур для подсобного хозяйства | Куры, индюки, гуси: какие породы мы держим и почему | Яйцо и птица | [ptitsa-porody](https://bestdeejay-design.github.io/fermaruna/articles/ptitsa-porody/) |
| 8 | купить суточных цыплят | Как выбрать суточных цыплят и подготовить дом для птенцов | Яйцо и птица | [ptency-pokupka](https://bestdeejay-design.github.io/fermaruna/articles/ptency-pokupka/) |
| 9 | картофель с целинных земель | Почему картофель с целинных земель вкуснее | Земля и метод | [celinne-zemli](https://bestdeejay-design.github.io/fermaruna/articles/celinne-zemli/) |
| 10 | натуральное земледелие без химии | Агротехнологии 1920-х: что мы переняли у дедов | Земля и метод | [agrotehnologii-1920h](https://bestdeejay-design.github.io/fermaruna/articles/agrotehnologii-1920h/) |
| 11 | инкубация яиц на ферме | Замкнутый цикл: как на ферме появляется птица | Земля и метод | [zamknutyy-cikl](https://bestdeejay-design.github.io/fermaruna/articles/zamknutyy-cikl/) |
| 12 | пчёлы карника | Пчёлы породы «Карника»: почему мы выбрали их | Мёд и пчёлы | [karnika](https://bestdeejay-design.github.io/fermaruna/articles/karnika/) |
| 13 | чем кормить кур без комбикорма | Зерно и трава вместо комбикорма: чем мы кормим птицу | Яйцо и птица | [zerno-i-trava](https://bestdeejay-design.github.io/fermaruna/articles/zerno-i-trava/) |
| 14 | фермерские продукты почему лучше | Почему фермерские продукты — это про доверие | Практика | [pochemu-fermerskoe](https://bestdeejay-design.github.io/fermaruna/articles/pochemu-fermerskoe/) |

## Перед запуском

- Проверьте факты о ферме (сорта, породы, сроки, наличие) — тексты опираются на то, что сказано на fermaruna.ru.
- Общие сведения (хранение, свежесть, сроки инкубации и т. п.) носят справочный характер. Они не заменяют рекомендации специалистов.
- Добавьте телефон и e-mail в `content/site.json`, замените иллюстрации реальными фотографиями и пересоберите сайт: `python3 scripts/build.py`.
- Зарегистрируйте сайт в Яндекс Вебмастере и Google Search Console, отправьте `sitemap.xml`.
- Для боевого домена задайте канонический адрес: `SITE_BASE_URL=https://fermaruna.ru python3 scripts/build.py`.
- Не публикуйте непроверенные отзывы, цены и обещания: на сайте их нет намеренно.
