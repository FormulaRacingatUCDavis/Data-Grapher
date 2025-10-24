import csv
import os
import cantools

root = os.path.dirname(os.path.abspath(__file__))
logs_dir = os.path.join(root, 'logs')
parsed_logs_dir = os.path.join(root, 'parsed')
os.makedirs(parsed_logs_dir, exist_ok=True)

frucd_dbc = cantools.database.load_file('20240129 Gen5 CAN DB.dbc')
mc_dbc = cantools.database.load_file('FE12.dbc')

for can_log in os.listdir(logs_dir):
    # Process raw CAN data CSV log
    log_path = os.path.join(logs_dir, can_log)

    parsed_msgs = []
    ids = set()
    signals = set()

    f_ids = set()
    f_count = 0

    print(f'\nParsing {can_log}...')
    with open(log_path, 'r', newline='') as raw_can:
        reader = csv.reader(raw_can)
        for row in reader:
            id_str = row[0]
            id = int(id_str, 16)

            # Process message using either FRUCD or MC DBC
            message = None
            for dbc in [frucd_dbc, mc_dbc]:
                try:
                    message = dbc.get_message_by_frame_id(id)
                    break
                except KeyError:
                    continue
            if message is None:
                # Message is not defined in DBCs
                print(f'>> Unrecognized ID {id} at timestamp: {row[-1]}')
                f_ids.add(id)
                f_count += 1
                continue

            data_bytes = []
            for b in row[1:9]:
                if b.strip() == "":
                    data_bytes.append(0)
                else:
                    try:
                        data_bytes.append(int(b))
                    except ValueError:
                        data_bytes.append(0)

            raw_data = bytes(data_bytes)
            timestamp = float(row[-1]) / 1000.0
            parsed_data = message.decode(raw_data)
            
            # [(Timestamp [s], Source, ID, Name, [Signal 1, Signal 2, ...]), ...]
            parsed_msgs.append((
                timestamp,
                message.senders[0],
                id_str,
                message.name,
                parsed_data
            ))

            # Keep track of CAN message signals logged
            if id_str not in ids:
                ids.add(id_str)
                for signal in message.signals:
                    signals.add(signal.name)

    # Output parsed CAN data as CSV
    parsed_log = can_log.replace('.csv', '_parsed.csv')
    parsed_log_path = os.path.join(parsed_logs_dir, parsed_log)

    with open(parsed_log_path, 'w', newline='') as parsed_can:
        # Timestamp [s]     Source     ID     Message     Signal 1     Signal 2...
        signals_list = sorted(signals)
        header = ['Timestamp [s]', 'Source', 'ID', 'Message'] + signals_list
        
        writer = csv.writer(parsed_can)
        writer.writerow(header)

        for timestamp, source, id_str, msg_name, decoded in parsed_msgs:
            row_data = [timestamp, source, id_str, msg_name]
            for sig in signals_list:
                value = decoded.get(sig, "")
                row_data.append(value)
            writer.writerow(row_data)

        print(f'>> Total failed rows: {f_count}')