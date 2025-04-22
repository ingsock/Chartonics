
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity test is
    port (
        clk     : in  std_logic;
        reset   : in  std_logic;

        -- Inputs
        T1      : in  std_logic;
        T2      : in  std_logic;
        T3      : in  std_logic;
        car     : in  std_logic;

        -- Outputs
        mg      : out std_logic;
        mr      : out std_logic;
        my      : out std_logic;
        sy      : out std_logic;
        sg      : out std_logic;
        sr      : out std_logic
    );
end entity test;

architecture Behavioral of test is

    -- State register and next state logic signals
    signal current_state, next_state : std_logic_vector(1 downto 0);

begin

    -- Combinational logic for next state and outputs
    process (current_state, T1, T2, T3, car)
    begin

        -- Next State Logic
        next_state(0) <= ((current_state(0)) and ((not T3))) or ((current_state(0)) and ((not current_state(1)))) or ((T1) and (current_state(1)) and ((not current_state(0))));
        next_state(1) <= ((T2) and (current_state(0)) and ((not current_state(1)))) or ((current_state(0)) and (current_state(1)) and ((not T3))) or ((current_state(1)) and ((not T1)) and ((not current_state(0)))) or ((car) and ((not current_state(0))) and ((not current_state(1))));

        -- Output Logic
        mg <= ((not current_state(0))) and ((not current_state(1)));
        mr <= current_state(0);
        my <= (current_state(1)) and ((not current_state(0)));
        sy <= (current_state(0)) and (current_state(1));
        sg <= (current_state(0)) and ((not current_state(1)));
        sr <= (not current_state(0));

    end process;

    -- State Register (Sequential logic)
    process (clk, reset)
    begin
        if reset = '1' then
            current_state <= "00"; -- Reset state
        elsif rising_edge(clk) then
            current_state <= next_state;
        end if;
    end process;

end architecture Behavioral;
