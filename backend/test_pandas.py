import pandas as pd

def test_minimal():
    html = """
    <table>
        <thead>
            <tr>
                <th>Symbol</th>
                <th>Company</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>MMM</td>
                <td>3M</td>
            </tr>
        </tbody>
    </table>
    """
    try:
        print("Testing read_html with lxml...")
        dfs = pd.read_html(html, flavor='lxml')
        print(f"Success lxml! found {len(dfs)} dfs")
        print(dfs[0])
    except Exception as e:
        print(f"Failed lxml: {e}")

    try:
        print("\nTesting read_html with bs4...")
        dfs = pd.read_html(html, flavor='bs4')
        print(f"Success bs4! found {len(dfs)} dfs")
        print(dfs[0])
    except Exception as e:
        print(f"Failed bs4: {e}")
        
    try:
        print("\nTesting read_html with html5lib...")
        dfs = pd.read_html(html, flavor='html5lib')
        print(f"Success html5lib! found {len(dfs)} dfs")
        print(dfs[0])
    except Exception as e:
        print(f"Failed html5lib: {e}")

if __name__ == "__main__":
    test_minimal()
