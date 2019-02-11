FROM discorario_base
COPY . .
RUN chmod a+x wkhtmltopdf.sh
CMD python /usr/discorario/src/discorario_bot.py > /dev/null &> /dev/null
