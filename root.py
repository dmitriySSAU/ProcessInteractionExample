import threading
import subprocess

FIRST_PROGRAM = "py first.py"
SECOND_PROGRAM = "py second.py"

proc_table = []
proc_handlers = []


def search_proc(id_: int) -> subprocess.Popen:
    for proc in proc_table:
        if proc['id'] == id_:
            return proc['obj']


class HandlerProc(threading.Thread):
    def __init__(self, proc_id: int, proc_obj: subprocess.Popen):
        threading.Thread.__init__(self)
        self._proc_id: int = proc_id
        self._proc_obj: subprocess.Popen = proc_obj

    def run(self) -> None:
        while self._proc_obj.poll() is None:
            try:
                output = self._proc_obj.stdout.readline()
                if not output:
                    break
            # Процесс завершается не мгновенно.
            # То есть условие while еще может успеть выполниться,
            # но чтение строки уже не пройдет и будет except.
            except ValueError:
                break
            request: str = output.decode("utf-8").rstrip()
            request_info: dict = self._parse_request(request)
            if request_info['cmd'] == "relay":
                self._relay_msg(request_info['info']['id'], request_info['info']['msg'])

            print("[PROCESS:" + str(self._proc_id) + "] " + request_info['info']['msg'])

    def _parse_request(self, request: str) -> dict:
        result = {
            "cmd": "",
            "info": {}
        }

        if request.find("SEND_TO") != -1:
            result['cmd'] = "relay"
            result['info'] = {
                "id": self._parse_id(request),
                "msg": self._parse_msg(request)
            }
        elif request.find("SEND") != -1:
            result['cmd'] = "receive"
            result['info'] = {
                "msg": self._parse_msg(request)
            }
        return result

    def _parse_id(self, request: str) -> int:
        start_id_index = request.find(":") + 1
        end_id_index = request.find("]")
        return int(request[start_id_index:end_id_index])

    def _parse_msg(self, request: str) -> str:
        start_msg_index = request.find("msg={") + 5
        end_msg_index = request.find("}")
        return request[start_msg_index:end_msg_index]

    def _relay_msg(self, receiver_id: int, receiver_msg: str) -> None:
        receiver_proc = search_proc(receiver_id)
        try:
            receiver_proc.communicate(input=receiver_msg.encode("utf-8"), timeout=0)
        except subprocess.TimeoutExpired:
            return


def start_example():
    first_proc = subprocess.Popen(FIRST_PROGRAM, stdout=subprocess.PIPE)
    second_proc = subprocess.Popen(SECOND_PROGRAM, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    proc_table.append({
        "id": 1,
        "obj": first_proc
    })
    proc_table.append({
        "id": 2,
        "obj": second_proc
    })

    for proc in proc_table:
        proc_handlers.append(HandlerProc(proc['id'], proc['obj']))
    for handler in proc_handlers:
        handler.start()
    for handler in proc_handlers:
        handler.join()


if __name__ == "__main__":
    start_example()
