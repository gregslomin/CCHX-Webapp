import logo from './logo.svg';
import './App.css';

import SortedTable from "./components/SortedTable";
import React, { useState, useEffect } from "react";
import axios from 'axios';

function App() {
  const [data, setData] = useState([]);

  useEffect(() => {
    (async () => {
      const result = await axios("/list_assets?type_id=49722");
      setData(result.data);
    })();
  }, []);

  const columns = React.useMemo(
      () => [
        {
          Header: "Item Type",
          accessor: "type_id" // accessor is the "key" in the data
        },
        {
          Header: "DPS %",
          accessor: "dps"
        },
        {
          Header: "Damage",
          accessor: "damage"
        },
        {
          Header: "Rate of Fire",
          accessor: "rof"
        }
      ],
      []
  );

  return (
      <div className="App">
              <button onClick={() => window.location = "/eve_auth/login"}><img src={"https://web.ccpgamescdn.com/eveonlineassets/developers/eve-sso-login-black-large.png"}></img></button>
          <button onClick={() => axios("/fetch_assets") }>Fetch Assets</button>
          <SortedTable columns={columns} data={data} />
      </div>
  );
}

export default App;
