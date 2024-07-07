
import numpy as np
class Encryptor:

# this class is to be rewrite

    def __init__(self,key_prime:int) -> None:
        self.public_key     = key_prime
        self.secret_parts_recieved   = {}
        self.secret_parts_returned   = {}


    def clear_secret_cache(self) -> None:
        self.secret_parts_recieved      = {}
        self.secret_parts_returned      = {}

    def record_secret_part(self,secret_part:np.array,carrier_index:int) -> None:
        self.secret_parts_recieved[carrier_index] = secret_part

    def process_secret_parts(self) -> None:
        # First summing up all values, which are np arrays
        total_secret = sum(self.secret_parts_recieved.values()) % self.public_key

        num_carriers = len(self.secret_parts_recieved)
        carrier_keys = list(self.secret_parts_recieved.keys())

        if num_carriers < 1:
            return  # Exit if there are no parts to process

        sum_parts = np.zeros_like(total_secret)  # Initialize sum of parts

        # Iterate over carriers except the last one
        for carrier_index in carrier_keys[:-1]:
            # Generate random parts for each carrier
            random_part = np.random.randint(0, self.public_key, size=total_secret.shape)
            self.secret_parts_returned[carrier_index] = random_part
            sum_parts += random_part  # Sum the parts to adjust later

        # Calculate the last part to ensure the sum modulo condition
        last_key = carrier_keys[-1]
        last_part = (total_secret - sum_parts) % self.public_key
        self.secret_parts_returned[last_key] = last_part

        # Ensure the final part aligns with the total secret's scale
        actual_sum = sum(self.secret_parts_returned.values())
        difference = total_secret - actual_sum
        self.secret_parts_returned[last_key] += difference

    def return_carrier_parts(self,carrier_index:int) -> np.array:
        return self.secret_parts_returned[carrier_index]