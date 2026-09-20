package dfb;

import jakarta.servlet.http.HttpServletRequest;
import java.sql.Connection;
import java.sql.SQLException;
import java.sql.Statement;

/** The exact flow `bifrost.security.java.servlet-parameter-to-jdbc` names. */
public final class Control {
    public void handle(HttpServletRequest request, Connection connection) throws SQLException {
        String name = request.getParameter("name");
        String sql = "SELECT * FROM users WHERE name = '" + name + "'";
        Statement statement = connection.createStatement();
        statement.execute(sql);
    }
}
